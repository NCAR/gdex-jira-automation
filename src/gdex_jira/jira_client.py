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

def get_last_checked_ticket():
    config = load_config()
    last_checked_ticket = config.get('last_checked_ticket')
    return last_checked_ticket

def get_projects():
    config = load_config()
    jira_test_server = config.get('jira_test_url')
    jira_prod_server = config.get('jira_prod_url')
    jira_email = config['contacts'].get('primary', 'caliepayne@ucar.edu')
    jira_api_token = os.environ.get('TEST_JIRA_API_TOKEN')

    jira = JIRA(options={'server': jira_test_server}, basic_auth=(jira_email, jira_api_token))
    projects = jira.projects()
    for project in projects:
        print(f"Project Name: {project.name}, Key: {project.key}")

def get_unassigned_tickets():
    pass

def change_status(ticket, status):
    pass


