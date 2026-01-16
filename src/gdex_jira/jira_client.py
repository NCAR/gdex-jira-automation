#!/usr/bin/env python
import sys
import os
import re
import json

import requests
from jira import JIRA

import json
from pathlib import Path
from typing import Any

def get_jira_connection(
        production: bool = True,
        prod_url= "https://ithelp.ucar.edu", 
        test_url= "https://stage-ithelp.ucar.edu") -> JIRA:
    
    server = prod_url if production else test_url
    api_token = os.environ.get('PROD_JIRA_API_TOKEN' if production else 'TEST_JIRA_API_TOKEN')
    if not api_token:
        raise EnvironmentError(
            f"{'PROD_JIRA_API_TOKEN' if production else 'TEST_JIRA_API_TOKEN'} is not set in environment variables."
        )

    jira_instance = JIRA(options={'server': server}, token_auth=api_token)
    return jira_instance

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

def _issue_to_dict(issue) -> dict[str, Any]:
    return {
        "key": _clean_text(issue.key),
        "reporter": {
            "name": _clean_text(issue.fields.reporter.displayName),
            "email": _clean_text(issue.fields.reporter.emailAddress),
        } if issue.fields.reporter else None,
        "summary": _clean_text(issue.fields.summary),
        "description": _clean_text(issue.fields.description),
        "created": _clean_text(issue.fields.created)
    }

def get_unassigned_service_tickets(jira_instance:str) -> list[dict[str, Any]]:
    jira = jira_instance

    issues = jira.search_issues(
        'project = "NSF NCAR Research Data Help Desk" '
        'AND assignee = DATAHELP-SERVICES-CONSULTING '
        'AND resolution = Unresolved '
        'ORDER BY key ASC',
        maxResults=50
    )

    tickets = [_issue_to_dict(issue) for issue in issues]
    return tickets


# Extract DSID from text in both formats: dxxxxxx or dsxxx.x
# dsxxx.x were mapped to dxxx00x in the new system
# call format_dataset_id from gdex-web-portal/api/common.py 
def get_dsid_from_json(json_text: json) -> str | None:
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

#Customer Comment 
def add_comment_to_ticket(jira_instance: JIRA, ticket_id: str, comment: str):
    try:
        jira_instance.add_comment(ticket_id, comment)
        print(f"Successfully added comment to ticket {ticket_id}")
    except Exception as e:
        print(f"Failed to add comment to ticket {ticket_id}: {e}")

#Comment restricted to internal team only
def add_internal_note_to_ticket(jira_instance: JIRA, ticket_id: str, note: str):
    try:
        jira_instance.add_comment(
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

def assign_jira_ticket(jira_instance: JIRA, ticket_id: str, email: str):
    try:
        jira_instance.assign_issue(ticket_id, email)
        print(f"Successfully assigned ticket {ticket_id} to {email}")
        note = f"Ticket assigned to {email} based on DSID ownership. This was done automatically via script. Please @-mention caliepayne@ucar.edu in regards to issues with script."
        add_internal_note_to_ticket(jira_instance, ticket_id, note)
    except Exception as e:
        print(f"Failed to assign ticket {ticket_id}: {e}")

def main():
    jira_instance = get_jira_connection() # Defaults are set to production
    ticket_list = get_unassigned_service_tickets(jira_instance)
    for ticket in ticket_list:
        ticket_id = ticket['key']
        print(f"Processing ticket {ticket_id}...")
        dsid = get_dsid_from_json(ticket['description'])
        if dsid:
            #print(f"Found DSID: {dsid} \n")
            email = get_dsid_owner_email(dsid)
            if email: 
                assign_jira_ticket(jira_instance, ticket_id, email)
                
            
        else:
            print(f"No DSID found.\n")

if __name__ == "__main__":
    main()

