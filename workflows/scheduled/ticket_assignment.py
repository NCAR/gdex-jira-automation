def assign_unassigned_tickets(jira_instance):
# 01_Assign Service Tickets
    service_ticket_list = jira_instance.get_unassigned_tickets(service=True)
    if not service_ticket_list:
        print("No unassigned service tickets found.")
    for ticket in service_ticket_list:
        jira_instance.assign_by_dsid(ticket)
# # 02_Assign_Curation_Tickets
#     curation_ticket_list = jira_instance.get_unassigned_tickets(service=False)
#     for curation_ticket in curation_ticket_list:
#         print(curation_ticket)





