#Intialize Jira client and run scheduled tasks
import os
from triager.triager import triage_tickets
from jira_client.helpers import GdexJiraAutomator as JiraAuto
# from workflows.scheduled.ticket_assignment import assign_unassigned_tickets

def main():
    # Load Jira Payload env variables
    ticket_id = os.getenv("PAYLOAD_TICKET_ID")
    print(ticket_id)

    #Intialize Jira client
    jira = JiraAuto(dry_run = False)

    #Incoming ticket package
    incoming_ticket = {'jira_instance': jira,
                       'ticket_id': ticket_id, 
                       'ticket_type':ticket_type}

    # triage ticket based on customer request type
    triage_tickets(incoming_ticket, jira)

if __name__ == "__main__":
    main()
