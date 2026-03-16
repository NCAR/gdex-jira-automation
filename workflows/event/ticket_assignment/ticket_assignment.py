def assign_unassigned_tickets(jira_instance, ticket_id):
# 01_Assign Service Tickets
    ticket_dict = jira_instance.get_unassigned_tickets(ticket_id= ticket_id)
    jira_instance.assign_by_dsid(ticket_dict)
