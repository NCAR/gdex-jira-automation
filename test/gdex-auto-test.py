#from gdex_jira.jira_client import get_last_checked_ticket

# def test_get_last_checked_ticket():
#     last_ticket = get_last_checked_ticket()
#     assert last_ticket == "DATAHELP-12349", f"Expected 'DATAHELP-12349', got '{last_ticket}'"

# def main():
#     test_get_last_checked_ticket()
#     print("All tests passed.")

# if __name__ == "__main__":
#     main()

import re 

text ="D609000"
dsid_patterns = [r'\bd\d{6}\b', r'\bds\d{3}\.\d\b']
for pattern in dsid_patterns:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        dsid = match.group().lower()
        print(dsid)


