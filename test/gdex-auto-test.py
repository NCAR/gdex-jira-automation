from gdex_jira.jira_client import get_last_checked_ticket

def test_get_last_checked_ticket():
    last_ticket = get_last_checked_ticket()
    assert last_ticket == "DATAHELP-12349", f"Expected 'DATAHELP-12349', got '{last_ticket}'"

def main():
    test_get_last_checked_ticket()
    print("All tests passed.")

if __name__ == "__main__":
    main()
