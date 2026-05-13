def generate_switch_status(jira_instance, ticket_details):
    ticket_id = ticket_details['key']
    issue = jira_instance.jira.issue(ticket_id)
    issue_status = issue.fields.status.id

    if jira_instance.dry_run:
        print(f"[DRY_RUN] Would switch {ticket_id} to Data Management Plan.")
        return
    # Switch from Open to Waiting for Customer to Data Management PLan
    if issue_status == "1": # Open
        jira_instance.jira.transition_issue(ticket_id, "181")
        jira_instance.jira.transition_issue(ticket_id, "161")
    else:
        print("Could not switch status.")
        







    