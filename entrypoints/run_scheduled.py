#Intialize Jira client and run scheduled tasks
#from jira_client.helpers import GdexJiraAutomator as JiraAuto
import sys
import os
# Add the root directory (gdex-jira-automation) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from workflows.scheduled.ticket_assignment import assign_unassigned_tickets

def main():
    jira = JiraAuto(dry_run = True)
    assign_unassigned_tickets(jira)

if __name__ == "__main__":
    main()
