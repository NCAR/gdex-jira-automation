def assign_unassigned_tickets(jira_instance, ticket_id):
# 01_Assign Service Tickets
    ticket_dict = jira_instance.get_unassigned_tickets(ticket_id= ticket_id)
    #message = "Thank you for submitting a ticket. GDEX services are currently down, and our team is actively working to restore them as soon as possible. We apologize for the inconvenience."
    #jira_instance.add_comment_to_ticket(ticket_id= ticket_id, comment= message)
    jira_instance.assign_by_dsid(ticket_dict)
