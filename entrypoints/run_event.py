#Intialize Jira client and run scheduled tasks
import os
from triager.triager import triage_tickets
from jira_client.helpers import GdexJiraAutomator as JiraAuto
from jira import JIRA, JIRAError
# from workflows.scheduled.ticket_assignment import assign_unassigned_tickets

def main():
    # Load Jira Payload env variables
    incoming_ticket_id = os.getenv("PAYLOAD_TICKET_ID", "DATAHELP-5708")

    #Intialize Jira client
    config_files = ["config/jira_config.yaml", "triager/workflow-mapping.yaml"]
    jira = JiraAuto(dry_run = True, config= config_files)
    
    #Grab ticket contents from Jira API and add to payload
    incoming_ticket_details = jira.get_unassigned_tickets(ticket_id = incoming_ticket_id)
    # print(f"Incoming ticket payload: {incoming_ticket_details}")

    # triage ticket based on customer request type
    triage_tickets(ticket_details = incoming_ticket_details, 
                   mapping_config = jira.triager_workflow, 
                   jira_object = jira)

if __name__ == "__main__":
    main()
