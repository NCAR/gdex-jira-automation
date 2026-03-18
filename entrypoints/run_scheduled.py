#Intialize Jira client and run scheduled tasks
from jira_client.helpers import GdexJiraAutomator as JiraAuto
from workflows.scheduled.ticket_assignment import assign_unassigned_tickets
from workflows.scheduled.stale_ticket_checker import comment_on_stale_tickets

def main():
#0. Intialize Jira client
    config_files = ["config/jira_config.yaml", "triager/workflow-mapping.yaml"]
    jira = JiraAuto(dry_run = False, config= config_files)

#1. workflows.scheduled.ticket_assignment
    assign_unassigned_tickets(jira)

#2. workflows.scheduled.stale_ticket_checker
    comment_on_stale_tickets(jira)

if __name__ == "__main__":
    main()
