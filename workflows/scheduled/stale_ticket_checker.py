
def comment_on_stale_tickets(jira_instance):
    jira_instance.get_stale_tickets()