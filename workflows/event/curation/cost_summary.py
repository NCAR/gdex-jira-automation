from jira_client.helpers import GdexJiraAutomator as JiraAuto

def generate_cost_summary (jira_instance, ticket_id):
    message = f"GENERATE COST SUMMARY for {ticket_id}"
    JiraAuto.add_comment_to_ticket(ticket_id, message)
