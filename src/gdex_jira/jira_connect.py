
import os
from jira import JIRA


def get_jira_connection():
    config = load_config()
    jira_test_server = config.get('jira_test_url')
    #jira_prod_server = config.get('jira_prod_url')
    server = jira_test_server
    print(server)
    jira_email = config['contacts'].get('primary', 'caliepayne@ucar.edu')
    print(jira_email)
    jira_api_token = os.environ.get('TEST_JIRA_API_TOKEN')
    jira = JIRA(options={'server': server},token_auth=jira_api_token)
    return jira