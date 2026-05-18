def prioritize_incoming_ticket(jira_instance, ticket_details):
    ticket_id = ticket_details['key']
    reporter_email = ticket_details["reporter_email"]
    international_tlds = {".uk", ".jp", ".de", ".fr", ".cn", ".au", ".ca"}

    if any(tld in reporter_email for tld in international_tlds):
        return

    if ".edu" in reporter_email:
        issue = jira_instance.jira.issue(ticket_id)
        issue.update(fields={"priority": {"name": "High"}})
        