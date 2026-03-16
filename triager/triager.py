#Intialize Jira client and run scheduled tasks
#from jira_client.helpers import GdexJiraAutomator as JiraAuto
#from workflows.scheduled.ticket_assignment import assign_unassigned_tickets
import yaml
import importlib

def get_workflow_function(path_str):
    """
    Convert path string (like
    'workflows.scheduled.ticket_assignment.assign_unassigned_tickets')
    into the actual callable function.
    Returns None if the path is empty or invalid.
    """
    if not path_str:
        return None
    
    *module_parts, func_name = path_str.split(".")
    module_path = ".".join(module_parts)

    try:
        # Split string into module path and function name
        *module_parts, func_name = path_str.split(".")
        module_path = ".".join(module_parts)
        # Import the module dynamically
        module = importlib.import_module(module_path)
        
        # Get the function from the module
        func = getattr(module, func_name)
        return func
    
    except (ModuleNotFoundError, AttributeError) as e:
        print(f"[ERROR] Could not load workflow function from '{path_str}': {e}")
        return None
    
def triage_tickets(ticket_details: dict, jira):

  with open("triager/workflow-mapping.yaml", "r") as f:
    mapping_yaml = yaml.safe_load(f)

  workflow_map = {}
  for group, info in mapping_yaml.items():
      workflow_map.update({ticket: info['workflow'] for ticket in info['tickets']})


  ticket_id = ticket_details["ticket_id"]
  workflow = workflow_map.get(ticket_details['ticket_type'])

  function = get_workflow_function(workflow)
  function(jira, ticket_id)

