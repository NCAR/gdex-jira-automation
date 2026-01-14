#!/usr/bin/env python
import sys
import os
import json

import requests
from jira import JIRA

import json
from pathlib import Path
from typing import Any

def load_config(filename: str = "config.json") -> Any:
    """
    Load a JSON config file located in the same directory as this module.

    Args:
        filename: Name of the JSON file (default "config.json").

    Returns:
        The parsed JSON object (dict, list, etc.).
    """
    config_path = Path(__file__).parent / filename

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_jira_connection():
    config = load_config()
    jira_test_server = config.get('jira_test_url')
    jira_prod_server = config.get('jira_prod_url')
    
    # switch between test and prod as needed
    server = jira_prod_server
    jira_email = config['contacts'].get('primary', 'caliepayne@ucar.edu')
    jira_api_token = os.environ.get('PROD_JIRA_API_TOKEN')
    jira_instance = JIRA(options={'server': server},token_auth=jira_api_token)
    return jira_instance

def get_last_checked_ticket():
    config = load_config()
    last_checked_ticket = config.get('last_checked_ticket')
    return last_checked_ticket

def get_unassigned_tickets(jira_connection):
    start_from_issue = get_last_checked_ticket()
    print(f"Starting from issue: {start_from_issue}")
    jira_instance = jira_connection
    issues = jira_instance.search_issues(
    f'project = "NSF NCAR Research Data Help Desk" AND assignee = DATAHELP-SERVICES-CONSULTING and resolution = Unresolved ORDER BY  key ASC',
    maxResults=50)
    ticket_list = [issue.key for issue in issues]
    return ticket_list

def get_ticket_contents(ticket_id: str):
    ticket_text = ""
    return ticket_text

def process_ticket(ticket_text: str):
    pass


def change_status(ticket, status):
    pass

def main():
    jira_instance = get_jira_connection()
    get_unassigned_tickets(jira_instance)


if __name__ == "__main__":
    main()

