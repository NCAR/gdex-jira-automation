def prioritize_incoming_ticket(jira_instance, ticket_details):
    ticket_id = ticket_details['key']
    reporter_email = ticket_details["reporter_email"]
    international_tlds = {".uk", ".jp", ".de", ".fr", ".cn", ".au", ".ca"}

    # Check if the reporter's email contains any international TLD
    if any(reporter_email.endswith(tld) for tld in international_tlds):
        return

    if reporter_email.endswith(".edu"):
        issue = jira_instance.jira.issue(ticket_id)
        issue.update(fields={"priority": {"name": "High"}})
        