#!/usr/bin/env python
import sys
import os
import re
import json
import logging
import random

import requests
from jira import JIRA, JIRAError
from collections import Counter

import json
from pathlib import Path
from typing import Any


class GdexJiraAutomator:
    def __init__(self, production_server: bool = True):
        try:
            self.jira = self._get_jira_connection(production=production_server)
            logging.info("Connected to JIRA successfully.")
        except EnvironmentError as e:
            logging.error(f"Environment variable missing: {e}")
            self.jira = None
        except JIRAError as e:
            logging.error(f"Failed to connect to JIRA: {e}")
            self.jira = None
        except requests.RequestException as e:
            logging.error(f"Network/API error when connecting to jira: {e}")
            self.jira = None
        except Exception as e:
            logging.error(f"Unexpected error during JIRA connection: {e}")
            self.jira = None

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
        cleaned = re.sub(r'\n{3,}', '\n', cleaned)
        cleaned = cleaned.strip()
        return cleaned

    def _issue_to_dict(self,issue) -> dict[str, Any]:

        """
        Converts a JIRA issue object to a cleaned dictionary.
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
        if not self.jira:
            logging.warning("Cannot check if ticket has been assigned before: Jira Connection not available.")
            return

        try:
            ticket = self.jira.issue(issue, expand='changelog')
        except JIRAError as e:
            logging.error(f"Failed to get Jira changelog for {issue}: {e}")
            return None
        
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
        if not self.jira:
            logging.warning("Cannot fetch unassigned tickets: Jira Connection not available.")
            return
        
        try:
            issues = self.jira.search_issues(
                f'project = "NSF NCAR Research Data Help Desk" '
                f'AND assignee = DATAHELP-{"SERVICES-CONSULTING" if service else "CURATION-SUPPORT"} '
                'AND resolution = Unresolved '
                'ORDER BY key ASC',
                maxResults=50
            )
        except JIRAError as e:
            logging.error(f"Failed to pull unassigned tickets from Jira: {e}")
            return None
        
        #only stores tickets that have not been assigned before
        tickets = [self._has_been_assigned_before(issue.key) for issue in issues]
        #convert to dict
        tickets = [self._issue_to_dict(issue) for issue in issues]
        return tickets

    @staticmethod
    def get_dsid_from_json(ticket_text: dict) -> str | None:

        """
        Extract DSID from JSON text using regex patterns.
        Args:
            json_text (json): The JSON text to search for DSID.
        Returns:
            str: The extracted DSID, or None if not found.
        """
        if not ticket_text:
            return None
        if not isinstance(ticket_text, dict):
            raise TypeError(f"Text must be in dict format, got {type(ticket_text).__name__}")
        
        dsid_patterns = [r'\bd\d{6}\b', r'\bds\d{3}\.\d\b']  # match d + 6 digits as a whole word

        for pattern in dsid_patterns:
            text = " ".join(map(str, ticket_text.values()))
            print(text)
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dsid = match.group().lower()
                # If the format is dsxxx.x, convert to dxxx00x
                # TODO: Consider dsid conversion to be its own function so it can be used elsewhere
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
        if not isinstance(dsid, str):
            raise TypeError(f"dsid must be a string, got {type(dsid).__name__}")
        
        # TODO: Check for dsid format here 
        
        url = f"https://gdex.ucar.edu/api/get_staff/{dsid}/"

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.ConnectionError as e:
            logging.error(f"Connection failed when trying to fetch DSID {dsid} from GDEX API: {e}")
            return None
        except requests.Timeout:
            logging.error(f"Request timed out while fetching DSID {dsid} from GDEX API.")
            return None
        except requests.HTTPError as e:
            logging.error(f"HTTP error {e.response.status_code} fetching DSID {dsid} from GDEX API: {e}")
            return None
        except requests.RequestException as e:
            logging.error(f"Network/API error fertching DSID {dsid} from GDEX API: {e}")
            return None

        try:
            json_data = response.json()
        except ValueError as e:
            print(f"Failed to decod JSON for {dsid} from GDEX API: {e}")
            return None
        
        try:
            if "data" in json_data and json_data["data"]:
                email = json_data["data"][0].get("email")
                if not email:
                    print(f"No email found for DSID {dsid} in GDEX API response")
                return email
            else:
                print(f"No staff data returned for DSID {dsid} from GDEX API: {e}")
                return None
        except (KeyError, TypeError) as e:
            print(f"Unexpected data structure for {dsid} via GDEX API: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error processing DSID {dsid} data via GDEX API: {e}")
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
            logging.info(f"Successfully added comment to ticket {ticket_id}")
        except JIRAError as e:
            logging.error(f"JIRA API error adding comment to ticket {ticket_id}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error adding comment to ticket {ticket_id}: {e}")

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
            logging.info(f"Successfully added internal note to ticket {ticket_id}")
        except JIRAError as e:
            logging.error(f"JIRA API error adding internal note to ticket {ticket_id}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error adding internal note to ticket {ticket_id}: {e}")

    def assign_jira_ticket(self, ticket_id: str, email: str, note):

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
            #note = f"Ticket assigned to {email} based on DSID ownership. This was done automatically via script. Please @-mention caliepayne@ucar.edu in regards to issues with script."
            self.add_internal_note_to_ticket(ticket_id, note)
        except JIRAError as e:
            logging.error(f"JIRA API error when assigning {ticket_id}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error assigning {ticket_id} to {email}: {e}")

def main():
    automator = GdexJiraAutomator(production_server=True)

    service_ticket_list = automator.get_unassigned_tickets(service=True)
    curation_ticket_list = automator.get_unassigned_tickets(service=False)
    for ticket in service_ticket_list:
        ticket_id = ticket['key']
        print(f"--------------{ticket_id}----------SERVICES")
        dsid = automator.get_dsid_from_json(ticket)
        if dsid:
            print(f"Found DSID: {dsid} \n")
            email = automator.get_dsid_owner_email(dsid)
            print(email)
            if email: 
                if email == 'chifan@ucar.edu':
                    assignee_list = ["dattore@ucar.edu", "rpconroy@ucar.edu", "caliepayne@ucar.edu", "davestep@ucar.edu", "tcram@ucar.edu", "chiaweih@ucar.edu"]
                    email = random.choice(assignee_list)
                    note = f" Chi-fan's ticket randomly assigned to {email}. This was done automatically via script. Please @-mention caliepayne@ucar.edu in regards to issues with script. \n \n Common issues below: \n \n OSDF Issue: Please add support@osg-htc.org as a ticket participant FIRST. Then, add a customer-visible comment (not an internal note) summarizing the issue so OSDF can view it. \n Spam: Change the assignee to it-helpabuse@ucar.edu. \n Not a DATAHELP ticket? Ask the customer to resubmit to the appropriate help desk. If you are unsure, point them to help@ucar.edu. Close the ticket."
                    automator.assign_jira_ticket(ticket_id, email, note)
                else:
                    note = f"Ticket assigned to {email} based on DSID ownership. This was done automatically via script. Please @-mention caliepayne@ucar.edu in regards to issues with script. \n \n Common issues below: \n \n OSDF Issue: Please add support@osg-htc.org as a ticket participant FIRST. Then, add a customer-visible comment (not an internal note) summarizing the issue so OSDF can view it. \n Spam: Change the assignee to it-helpabuse@ucar.edu. \n Not a DATAHELP ticket? Ask the customer to resubmit to the appropriate help desk. If you are unsure, point them to help@ucar.edu. Close the ticket."
                    automator.assign_jira_ticket(ticket_id, email, note)   
        else:
            print(f"No DSID found.\n")
    
    for ticket in curation_ticket_list:
        ticket_id = ticket['key']
        print(f"--------------{ticket_id}----------CURATION")


if __name__ == "__main__":
    main()

