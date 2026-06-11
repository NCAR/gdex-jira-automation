# Internal Packages
from jira_automation.helpers import GdexJiraAutomator as JiraAuto

# External packages
from datetime import datetime
import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


class GoogleSheetsClient:
    def __init__(self, credentials):
        self.service = build("sheets", "v4", credentials=credentials)

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]

class GoogleDriveClient:
    def __init__(self):
        self.creds = self._authenticate()
        self.service = build("drive", "v3", credentials=self.creds)

    def _authenticate(self):
        creds = None

        # =========================
        # 1. LOAD TOKEN (CI OR LOCAL FILE)
        # =========================
        token_info = None

        if "GOOGLE_TOKEN" in os.environ:
            token_info = json.loads(os.environ["GOOGLE_TOKEN"])
        elif os.path.exists("token.json"):
            with open("token.json") as f:
                token_info = json.load(f)

        if token_info:
            creds = Credentials.from_authorized_user_info(token_info, DRIVE_SCOPES)

        # =========================
        # 2. REFRESH IF POSSIBLE
        # =========================
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        # =========================
        # 3. LOCAL ONLY OAUTH FLOW
        # =========================
        if not creds or not creds.valid:
            # BLOCK CI FROM EVER ENTERING THIS PATH
            if "GITHUB_ACTIONS" in os.environ:
                raise RuntimeError(
                    "Missing valid GOOGLE_TOKEN in GitHub Actions. "
                    "OAuth flow is disabled in CI."
                )

            if "GOOGLE_CREDENTIALS" in os.environ:
                client_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
                flow = InstalledAppFlow.from_client_config(client_info, DRIVE_SCOPES)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json",
                    DRIVE_SCOPES
                )

            creds = flow.run_local_server(
                port=0,
                access_type="offline",
                prompt="consent"
            )

            # Save locally ONLY
            with open("token.json", "w") as f:
                f.write(creds.to_json())

        return creds

    def _build_service(self):
        """Builds the Google Drive service."""
        self.service = build("drive", "v3", credentials=self.creds)

    def list_files(self, page_size=10):
        """Lists files from Google Drive."""
        try:
            results = (
                self.service.files()
                .list(pageSize=page_size, fields="nextPageToken, files(id, name)")
                .execute()
            )
            return results.get("files", [])
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
        
    def copy_file(self, file_id, new_name, destination_folder_id):
        """
        Copies a file to a specific folder.

        :param client: Authenticated Drive client
        :param file_id: ID of the file to copy
        :param new_name: Name for the copied file
        :param destination_folder_id: Folder ID to copy into
        """
        try:
            body = {
                "name": new_name,
                "parents": [destination_folder_id],
            }

            copied_file = self.service.files().copy(
                fileId=file_id,
                body=body,
                supportsAllDrives=True
            ).execute()

            return copied_file
        except HttpError as error:
            print(f"Error copying file: {error}")
            return None
    
def get_fiscal_year(date:str):
    dt = datetime.strptime(date[:10], "%Y-%m-%d")
    if dt.month >= 10:   # Oct–Dec
        return dt.year + 1
    else:                # Jan–Sep
        return dt.year
def update_google_sheets(updates:dict):
    pass

def generate_cost_summary(jira_instance, ticket_details):
    # Feed ticket_id information dict to ths function (FY, data_size, and waiver bools)
    ticket_id = ticket_details['key']
    date_created = ticket_details['created']
    fiscal_year = get_fiscal_year(date_created)
    # TODO: Create FY_cost_summary map
    if ticket_details['data_size_tb']:
        data_size_tb = float(ticket_details['data_size_tb'])
    else:
        return
    # Yes to waived means services are not required (False), vice versa.
    flip_map = {
    "Yes": "False",
    "No": "True"}
    dmss_waived = flip_map.get(ticket_details['dmss_waived'])
    dmps_waived = flip_map.get(ticket_details['dmps_waived'])
    title = ticket_details['summary']
    reporter_email = ticket_details['reporter_email']
    proposal_id = ticket_details['proposal_id']
    lab = ticket_details['lab']
    
    
    if ticket_details['data_size_tb'] >= 10:
        if jira_instance.dry_run:
            print(f"[DRY_RUN] Would generate cost summary for {ticket_id}")
            return
        drive = GoogleDriveClient()
        sheets = GoogleSheetsClient(drive.creds)
        

        file = drive.service.files().get(
        fileId="14TMWF-qqxKyWt5D_eE8XD2j0wfoFRxoYVP5MbiNbvQ4",
        fields="id, name, parents",
        supportsAllDrives=True).execute()
        #print(file)

        file_to_copy_id = '14TMWF-qqxKyWt5D_eE8XD2j0wfoFRxoYVP5MbiNbvQ4'
        folder_id = '1WXrvMO4QgplHYkYr0xL42hF6jwHGSX1V'

        new_file_name = f'FY{fiscal_year}_GDEX_DataManagementServices_Budget_{ticket_id}'
        file = drive.copy_file(file_to_copy_id, new_file_name, folder_id)
        if file:
            file_id = file.get("id")

            # Make file readable by anyone with the link
            drive.service.permissions().create(
                fileId=file_id,
                body={
                    "type": "anyone",
                    "role": "reader"
                },
                supportsAllDrives=True
            ).execute()

            # Update values in the sheet.
            body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": "B1", "values": [[date_created[:10]]]},
                    {"range": "B2", "values": [[ticket_id]]},
                    {"range": "B3", "values": [[title]]},
                    {"range": "B4", "values": [[proposal_id]]},
                    {"range": "B5", "values": [[reporter_email]]},
                    {"range": "B6", "values": [[lab]]},
                    {"range": "B8", "values": [[data_size_tb]]},
                    {"range": "B9", "values": [[dmps_waived]]},
                    {"range": "B10", "values": [[dmss_waived]]},
                ]
            }

            sheets.service.spreadsheets().values().batchUpdate(
                spreadsheetId=file_id,
                body=body
            ).execute()

            # Get a usable URL
            file_url = f"https://drive.google.com/file/d/{file_id}/view"
            message = f"A cost summary was generated for {ticket_id}:\n {file_url}.\n\nData Size (TB): {data_size_tb}\nData Management Processing Services (DMPS) Required: {dmps_waived}\nData Management Storage Services Required: {dmss_waived}  \n\nNOTE: This FY{fiscal_year} estimate is based on user input and may not be accurate. Please confirm data size and cost waivers with ticket submitter. \n[JIRA_AUTO__COST_SUMMARY] "
            jira_instance.add_comment_to_ticket(comment=message, ticket_id=ticket_id)
        else:
            return None


