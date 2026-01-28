#!/usr/bin/env python
import sys
import os
import re
import json

import requests
from jira import JIRA
from collections import Counter

import json
from pathlib import Path
from typing import Any


class GdexJiraAutomator:
    def __init__(self, production_server: bool = True):
        self.jira = self._get_jira_connection(production=production_server)

    def _get_jira_connection(
            self,
            production: bool = True,
            prod_url= "https://ithelp.ucar.edu", 
            test_url= "https://stage-ithelp.ucar.edu") -> JIRA:
        """
        Establishes a connection to the JIRA instance.
        Uses environment variables for API tokens:
        - PROD_JIRA_API_TOKEN for production
        - TEST_JIRA_API_TOKEN for test/staging      
        """
        
        server = prod_url if production else test_url
        api_token = os.environ.get('PROD_JIRA_API_TOKEN' if production else 'TEST_JIRA_API_TOKEN')
        if not api_token:
            raise EnvironmentError(
                f"{'PROD_JIRA_API_TOKEN' if production else 'TEST_JIRA_API_TOKEN'} is not set in environment variables."
            )

        jira_instance = JIRA(options={'server': server}, token_auth=api_token)
        return jira_instance

    @staticmethod
    def _clean_text(text: str) -> str|None:
        
        """
        Remove markup text (e.g. {color}, {code...})
        """
    
        if not text:
            return None

        cleaned = re.sub(r'\{[^}]*\}', '', text)
        cleaned = re.sub(r'\s+\n', '', cleaned)
        cleaned = re.sub(r'\n{3,}', '', cleaned)
        cleaned = cleaned.strip()
        return cleaned

    def _issue_to_dict(self,issue) -> dict[str, Any]:
        """
        Converts a JIRA issue object to a claned dictionary.
        """
        return {
            "key": self._clean_text(issue.key),
            "reporter": {
                "name": self._clean_text(issue.fields.reporter.displayName),
                "email": self._clean_text(issue.fields.reporter.emailAddress),
            } if issue.fields.reporter else None,
            "summary": self._clean_text(issue.fields.summary),
            "description": self._clean_text(issue.fields.description),
            "created": self._clean_text(issue.fields.created)
        }

    def _has_been_assigned_before(self, issue:str) -> dict[str, bool]:
        """
        Check if a JIRA issue has been assigned to DATAHELP-SERVICES-CONSULTING or DATAHELP-CURATION-SUPPORT more than once.
        Args:
            issue (str): The JIRA issue key.
        Returns:
            dict: A dictionary representing the issue.
        """

        ticket = self.jira.issue(issue, expand='changelog')
        history = []
        for item in ticket.changelog.histories:
            for change in item.items:
                if change.field == 'assignee':
                    history.append(change.toString)
        DATAHELP_count = Counter(history)
        if DATAHELP_count["DATAHELP-SERVICES-CONSULTING"] > 1 or DATAHELP_count["DATAHELP-CURATION-SUPPORT"] > 1:
            print(f"Issue {ticket.key} has been assigned before.")
            ticket_info = [ticket.key, True]
            print(ticket_info)
            return ticket_info
        else:
            return [ticket.key, True]
            

    def get_unassigned_tickets(
            self,
            service:bool=True) -> list[dict[str, Any]]:
        """
        Fetch unassigned tickets from JIRA for either Services Consulting or Curation Support.
        Args:
            jira_instance (JIRA): The JIRA instance to query.
            service (bool): If True, fetch tickets for Services Consulting; if False, for Curation Support.    
        Returns:
            list[dict]: A list of dictionaries representing unassigned tickets.
        """
        issues = self.jira.search_issues(
            f'project = "NSF NCAR Research Data Help Desk" '
            f'AND assignee = DATAHELP-{"SERVICES-CONSULTING" if service else "CURATION-SUPPORT"} '
            'AND resolution = Unresolved '
            'ORDER BY key ASC',
            maxResults=50
        )
        #only stores tickets that have not been assigned before
        tickets = [self.has_been_assigned_before(issue.key) for issue in issues]
        #convert to dict
        tickets = [self._issue_to_dict(issue) for issue in issues]
        return tickets

    @staticmethod
    def get_dsid_from_json(json_text: json) -> str | None:
        """
        Extract DSID from JSON text using regex patterns.
        Args:
            json_text (json): The JSON text to search for DSID.
        Returns:
            str: The extracted DSID, or None if not found.
        """
        dsid_patterns = [r'\bd\d{6}\b', r'\bds\d{3}\.\d\b']  # match d + 6 digits as a whole word
        if not json_text:
            return None
        for pattern in dsid_patterns:
            match = re.search(pattern, json_text)
            if match:
                dsid = match.group(0)
                # If the format is dsxxx.x, convert to dxxx00x
                if dsid.startswith('ds'):
                    parts = dsid[2:].split('.')
                    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                        dsid = f'd{parts[0]}00{parts[1]}'
                        return dsid
                else:
                    return dsid
        return None
            
    @staticmethod
    def get_dsid_owner_email(dsid:str) -> str | None:
        """
        Fetch the staff email for a given DSID from the UCAR GDEX API.

        Args:
            dsid (str): The DSID of the staff member.

        Returns:
            str: The email of the staff member, or None if not found/error.
        """
        url = f"https://gdex.ucar.edu/api/get_staff/{dsid}/"
        try:
            response = requests.get(url)
            response.raise_for_status()
            json_data = response.json()
            
            if "data" in json_data and json_data["data"]:
                email = json_data["data"][0].get("email")
                return email
            else:
                return None
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            return None

    
    def add_comment_to_ticket(self, ticket_id: str, comment: str):
        """
        Adds a customer comment to a JIRA ticket.
        Args:
            jira_instance (JIRA): The JIRA instance.
            ticket_id (str): The ID of the ticket to add the comment to.
            comment (str): The comment text to add.
        Returns:
            None
        """
        try:
            self.jira.add_comment(ticket_id, comment)
            print(f"Successfully added comment to ticket {ticket_id}")
        except Exception as e:
            print(f"Failed to add comment to ticket {ticket_id}: {e}")

    #Comment restricted to internal team only
    def add_internal_note_to_ticket(self, ticket_id: str, note: str):
        """
        Adds an internal note to a JIRA ticket via internal comment.
        Args:
            jira_instance (JIRA): The JIRA instance.
            ticket_id (str): The ID of the ticket to add the note to.
            note (str): The note text to add.
        Returns:
            None
        """
        try:
            self.jira.add_comment(
                ticket_id,
                note,
                visibility={
                    "type": "role",
                    "value": "Service Desk Team"
                }
            )
            print(f"Successfully added internal note to ticket {ticket_id}")
        except Exception as e:
            print(f"Failed to add internal note to ticket {ticket_id}: {e}")

    def assign_jira_ticket(self, ticket_id: str, email: str):
        """
        Assigns a JIRA ticket to a user.
        Args:
            jira_instance (JIRA): The JIRA instance.
            ticket_id (str): The ID of the ticket to assign.
            email (str): The email of the user to assign the ticket to.
        Returns:
            None
        """
        try:
            self.jira.assign_issue(ticket_id, email)
            print(f"Successfully assigned ticket {ticket_id} to {email}")
            note = f"Ticket assigned to {email} based on DSID ownership. This was done automatically via script. Please @-mention caliepayne@ucar.edu in regards to issues with script."
            self.add_internal_note_to_ticket(ticket_id, note)
        except Exception as e:
            print(f"Failed to assign ticket {ticket_id}: {e}")

def main():
    automator = GdexJiraAutomator(production_server=True)
    automator.has_been_assigned_before("DATAHELP-5596")

    # service_ticket_list = automator.get_unassigned_tickets(service=True)
    # curation_ticket_list = automator.get_unassigned_tickets(service=False)
    # for ticket in service_ticket_list:
    #     ticket_id = ticket['key']
    #     print(f"--------------{ticket_id}----------SERVICES")
    #     dsid = automator.get_dsid_from_json(ticket['description'])
    #     if dsid:
    #         print(f"Found DSID: {dsid} \n")
    #         email = automator.get_dsid_owner_email(dsid)
    #         print(email)
    #         if email: 
    #             automator.assign_jira_ticket(ticket_id, email)   
    #     else:
    #         print(f"No DSID found.\n")
    
    # for ticket in curation_ticket_list:
    #     ticket_id = ticket['key']
    #     print(f"--------------{ticket_id}----------CURATION")


if __name__ == "__main__":
    main()

