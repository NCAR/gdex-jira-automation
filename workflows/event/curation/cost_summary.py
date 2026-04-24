from jira_client.helpers import GdexJiraAutomator as JiraAuto

def generate_cost_summary (jira_instance, ticket_id):
    message = f"GENERATE COST SUMMARY for {ticket_id}"
    jira_instance.add_comment_to_ticket(comment=message, ticket_id=ticket_id)
