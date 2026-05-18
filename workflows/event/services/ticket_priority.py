def prioritize_incoming_ticket(jira_instance, ticket_details):
    ticket_id = ticket_details['key']
    reporter_email = ticket_details["reporter_email"]
    high_priority_domain_ext = ".edu"
    if high_priority_domain_ext in reporter_email:
        print(f"Ticket {ticket_id} moved to high priority.")
        issue = jira_instance.jira.issue(ticket_id)
        issue.update(fields=
            {"priority": {"name": "High"}
             })
        