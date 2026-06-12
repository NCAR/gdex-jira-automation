# Developer Guide

This guide is for team members maintaining or extending this automation. It assumes familiarity with Python and GitHub Actions, but not necessarily with this codebase.

---

## Glossary

| Term | Meaning |
|---|---|
| **DATAHELP** | The NSF NCAR Research Data Help Desk Jira project (`ithelp.ucar.edu`) |
| **GDEX** | Geoscience Data Exchange — the system this automation supports |
| **DSID** | Dataset identifier (e.g. `d123456` or `ds123.4`). Used to look up the dataset owner |
| **DDA** | GDEX Data Deposit Agreement — a PDF that external data submitters must acknowledge |
| **DMPS** | Data Management Processing Services |
| **DMSS** | Data Management Storage Services |
| **Lab** | A Jira custom field. `External` means the submitter is outside UCAR |
| **Fiscal Year** | UCAR follows a federal fiscal year: October 1 – September 30 |

---

## Architecture

### How Jira triggers GitHub Actions

A Jira automation rule sends a `repository_dispatch` webhook to this repo whenever a matching ticket event fires. The payload includes `ticket_id`. GitHub Actions receives this under the `jira-event` dispatch type and runs `jira_event.yml`.

> The Jira automation rule itself lives in the DATAHELP Jira project settings, not in this repo. If the trigger stops working, check there first.

### Event-driven flow

```
Jira automation rule
  → POST /repos/.../dispatches  (type: jira-event, payload: {ticket_id})
    → jira_event.yml
      → run_event.py
        → GdexJiraAutomator.get_unassigned_tickets(ticket_id)   # fetches ticket fields
          → triager.triage_tickets()                             # reads workflow-mapping.yaml
            → one or more workflow functions                     # do the actual work
```

### Scheduled flow

```
cron: every 12 hours
  → scheduled_event.yml
    → run_scheduled.py
      → assign_unassigned_tickets()   # batch-assigns service tickets by DSID
      → comment_on_stale_tickets()    # warns + auto-closes inactive tickets
```

---

## Setup

### Prerequisites

- Python 3.11
- Access to the `GDEX_JIRA_PRODUCTION_ENV` GitHub Actions environment (for secrets)
- A Jira API token for the production or staging server

### Install dependencies

```bash
pip install -r requirements.txt
```

### Environment variables

| Variable | Description |
|---|---|
| `PROD_JIRA_API_TOKEN` | API token for `ithelp.ucar.edu` |
| `TEST_JIRA_API_TOKEN` | API token for `stage-ithelp.ucar.edu` |
| `GOOGLE_CREDENTIALS` | JSON content of the Google OAuth client config |
| `GOOGLE_TOKEN` | JSON content of the Google OAuth token |
| `PAYLOAD_TICKET_ID` | Ticket ID passed in from Jira (set automatically in CI; set manually for local runs) |

For local development, export these before running scripts:

```bash
export PROD_JIRA_API_TOKEN=your_token_here
export PAYLOAD_TICKET_ID=DATAHELP-1234
```

---

## Running locally

### Dry run mode

`GdexJiraAutomator` accepts a `dry_run=True` flag. When set, it prints what it *would* do instead of making real Jira API calls. Use this for testing logic without side effects.

To test an event-driven run locally, edit `entrypoints/run_event.py` temporarily:

```python
jira = JiraAuto(dry_run=True, config=config_files)
```

Then run:

```bash
PYTHONPATH=. PROD_JIRA_API_TOKEN=your_token PAYLOAD_TICKET_ID=DATAHELP-1234 python entrypoints/run_event.py
```

### Staging server

To point at the staging Jira instance instead of production, change `production_server=True` to `production_server=False` in the entrypoint, and set `TEST_JIRA_API_TOKEN` instead of `PROD_JIRA_API_TOKEN`.

---

## Google API credentials

Google Drive and Sheets are used by `cost_summary.py`. Authentication works differently in CI vs. locally:

**In GitHub Actions:** The `GOOGLE_CREDENTIALS` and `GOOGLE_TOKEN` secrets are injected as environment variables. The code reads them directly — no files needed.

**Locally:** Place `credentials.json` (OAuth client config) and `token.json` (OAuth token) in the repo root. If `token.json` is missing or expired, the code will launch a local browser OAuth flow to generate one. Save the resulting `token.json` somewhere safe — it is gitignored.

> Do not commit `credentials.json` or `token.json`. They are in `.gitignore`.

When the token expires in CI, update the `GOOGLE_TOKEN` secret in the `GDEX_JIRA_PRODUCTION_ENV` GitHub Actions environment with a fresh token generated locally.

---

## How to add a new workflow

A "workflow" is any Python function with the signature:

```python
def my_workflow(jira_instance: GdexJiraAutomator, ticket_details: dict):
    ...
```

`ticket_details` is a dictionary with these keys (populated from Jira fields):

| Key | Description |
|---|---|
| `key` | Ticket ID (e.g. `DATAHELP-1234`) |
| `reporter_name` | Full name of the submitter |
| `reporter_email` | Email of the submitter |
| `summary` | Ticket title |
| `description` | Ticket body text |
| `created` | ISO timestamp of ticket creation |
| `request_type` | Jira service desk request type name |
| `data_size` | Human-readable size field from Jira |
| `data_size_tb` | Numeric size in TB |
| `dmss_waived` | `"Yes"` or `"No"` |
| `dmps_waived` | `"Yes"` or `"No"` |
| `lab` | Lab or affiliation (e.g. `"External"`) |
| `proposal_id` | Associated proposal ID |

**Steps:**

1. Create your function in `workflows/event/<category>/my_workflow.py` (or `workflows/scheduled/` for cron work).

2. Register it in `triager/workflow-mapping.yaml` using the full dotted module path:

```yaml
workflow_map:
  My New Category:
    workflow: workflows.event.my_category.my_workflow.my_workflow_function
    tickets:
      - My Jira Request Type Name
```

   For multiple workflows on the same request type, use a list:

```yaml
    workflow:
      - workflows.event.my_category.step_one.run
      - workflows.event.my_category.step_two.run
```

3. The triager loads and calls these functions dynamically — no import changes needed anywhere else.

---

## How to add a new request type to an existing workflow

In `triager/workflow-mapping.yaml`, add the Jira request type name (must match exactly) to the `tickets` list of the relevant group:

```yaml
  Service Tickets:
    workflow: ...
    tickets:
      - General Data Help
      - My New Request Type    # <-- add here
```

The request type name comes from `issue.fields.customfield_10001.requestType.name` in Jira.

---

## Automation behavior reference

### Stale ticket checker (scheduled)

- Runs every 12 hours.
- Flags tickets not updated in **14+ days** with a warning comment tagged `[JIRA_AUTO__STALE_TICKET]`.
- If a stale-tagged ticket still has no activity after **6 more days**, it is transitioned to Resolved and tagged `[JIRA_AUTO__CLOSE_TICKET]`.
- Tickets with priority **Hold** are skipped entirely.

### Cost summary (event-driven)

- Triggers on: `Suggest Dataset for GDEX`, `Submit Your Data to GDEX`, `Request for a proposal data management plan and budget`.
- Only runs if `data_size_tb >= 10`.
- Copies the Google Drive cost summary template into the shared GDEX folder, fills in ticket fields, and posts the link as an internal comment tagged `[JIRA_AUTO__COST_SUMMARY]`.
- Template file ID and destination folder ID are hardcoded in `cost_summary.py`. The `config/fy_cost_summary_map.yaml` is a placeholder for future per-fiscal-year config.

### DDA response (event-driven)

- Triggers on: `Submit Your Data to GDEX`.
- Only runs if `lab == "External"`.
- Downloads the DDA PDF from `gdex.ucar.edu`, overlays the submitter's name, email, and UTC timestamp, attaches it to the ticket, and posts a customer-visible comment.

### Ticket assignment — event (event-driven)

- Triggers on service request types.
- Extracts a DSID from the ticket text using regex (`d######` or `ds###.#` format).
- Calls the GDEX API (`gdex.ucar.edu/api/get_staff/{dsid}/`) to get the dataset owner's email.
- Assigns the ticket to that email and posts an internal note.

### Ticket assignment — scheduled (cron)

- Finds tickets currently assigned to `DATAHELP-SERVICES-CONSULTING` that are unresolved.
- Applies the same DSID-based assignment logic as above in batch.

### Ticket priority (event-driven)

- Triggers on service request types.
- Sets priority to **Low** for international email domains (`.uk`, `.jp`, `.de`, `.fr`, `.cn`, `.au`, `.ca`).
- Sets priority to **High** for `.edu` addresses.

---

## Debugging

### GitHub Actions runs

All workflow runs are visible under the **Actions** tab in GitHub. Each step's stdout is logged. Look for `[ERROR]` lines from Python logging or `curl` output from the connectivity test step.

The `jira_event.yml` workflow has a duplicate "Test Jira connectivity" step — this is a known redundancy and can be cleaned up.

### Checking which workflow was triggered

The triager prints the full `ticket_details` dict at the start of `triage_tickets()`. In a failed run, find the step output for "Run Jira Client" and look for that print.

### Manually triggering a run

Both workflows support `workflow_dispatch`, so you can trigger them manually from the Actions tab with any ticket ID — no need to wait for a real Jira event.

### Common failure modes

| Symptom | Likely cause |
|---|---|
| Jira connectivity step fails (401) | `PROD_JIRA_API_TOKEN` secret is expired or misconfigured |
| Google Drive copy fails in CI | `GOOGLE_TOKEN` secret is expired — regenerate locally and update the secret |
| Workflow function not called | Request type string in the ticket doesn't exactly match `workflow-mapping.yaml` |
| DSID not found | Ticket text doesn't contain a recognizable DSID pattern |
| Cost summary skipped | `data_size_tb` is below 10 or is `None` (submitter left the field blank) |

---

## Known gaps / TODOs

- `config/jira_field_mapping.yaml` and `utils/logger.py` are empty — stubs for future use.
- `workflows/event/curation/fy_cost_summary_map.yaml` has empty `file_id`/`folder_id` entries — intended to make the cost summary template configurable per fiscal year, but not yet wired up.
- `helpers.py` has a `assign_by_dsrqst` method that is incomplete.
- The curation ticket assignment branch in `workflows/scheduled/ticket_assignment.py` is commented out.
- DSID format conversion (`ds###.#` → `d###00#`) is inline and flagged for extraction into its own utility function.
