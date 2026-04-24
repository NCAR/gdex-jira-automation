# Internal Packages
from jira_client.helpers import GdexJiraAutomator as JiraAuto

# External packages
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class google_api:
    def __init__(self, google_api_token:str, dry_run: bool = False):
        self.dry_run = dry_run
        # Set Google API token in ubuntu secrets
        # Set Google API token in Github secrets
        # Set Google API credentials in Github secrets
        # Add credentials to workflow file
        # Add env var to workflow file


def generate_cost_summary (jira_instance, ticket_id):
    message = f"GENERATE COST SUMMARY for {ticket_id}"
    jira_instance.add_comment_to_ticket(comment=message, ticket_id=ticket_id)
