#!/usr/bin/env python
import sys
import os
import json

import requests
from jira import JIRA

config = json.load(open('config.json'))

def get_projects():
    jira_server = config.get('jira_prod_url')
    jira_email = config['contacts'].get('primary', 'rpconroy@ucar.edu')
    jira_api_token = os.environ.get('JIRA_API_TOKEN')

    jira = JIRA(options={'server': jira_server}, basic_auth=(jira_email, jira_api_token))

    projects = jira.projects()
    for project in projects:
        print(f"Project Name: {project.name}, Key: {project.key}")

def get_unassigned_tickets():
    pass

def change_status(ticket, status):
    pass


