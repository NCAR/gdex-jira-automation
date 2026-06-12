![DATAHELP Banner](images/DATAHELP_banner.png)

## Overview

Automation for handling [DATAHELP](https://ithelp.ucar.edu) Jira tickets using GitHub Actions. Supports two modes: event-driven (triggered per ticket) and scheduled (cron-based batch processing).

---

## Documentation

- [Developer Guide](docs/developer-guide.md) — setup, local development, how to add workflows, debugging

---

## How It Works

### Event-Driven (`jira_event.yml`)
Triggered via `repository_dispatch` when a Jira ticket event fires. The incoming ticket ID is passed as a payload, processed by `run_event.py`, and routed through the triager to the appropriate workflow(s).

### Scheduled (`scheduled_event.yml`)
Runs every 12 hours via cron. Executes `run_scheduled.py`, which scans for unassigned tickets and flags stale ones.

---

## Directory Structure

```
.
├── .github/workflows/
│   ├── jira_event.yml          # Event-driven workflow (repository_dispatch trigger)
│   └── scheduled_event.yml     # Cron workflow (every 12 hours)
│
├── entrypoints/
│   ├── run_event.py            # Entry point for event-driven runs
│   └── run_scheduled.py        # Entry point for scheduled runs
│
├── triager/
│   ├── triager.py              # Routes tickets to the correct workflow(s) based on request type
│   └── workflow-mapping.yaml   # Maps Jira request types to workflow handler functions
│
├── workflows/
│   ├── event/
│   │   ├── curation/
│   │   │   ├── auto_response/
│   │   │   │   └── dda_response.py     # Attaches a signed DDA PDF for external submitters
│   │   │   ├── cost_summary.py         # Generates a Google Drive cost summary sheet
│   │   │   └── switch_status.py        # Transitions ticket status (e.g. Open → DMP)
│   │   └── services/
│   │       ├── ticket_assignment.py    # Assigns ticket to DSID owner
│   │       └── ticket_priority.py      # Sets priority based on reporter email domain
│   └── scheduled/
│       ├── stale_ticket_checker.py     # Comments on + auto-closes stale tickets
│       └── ticket_assignment.py        # Batch-assigns unassigned service tickets
│
├── jira_automation/
│   └── helpers.py              # GdexJiraAutomator class — Jira API wrapper + core operations
│
├── config/
│   ├── jira_config.yaml        # Prod/staging server URLs and API token env var names
│   └── jira_field_mapping.yaml # Custom field mappings
│
└── utils/
    ├── config_loader.py        # Loads and merges YAML config files
    └── logger.py               # Logging setup
```

---

## Ticket Routing

The triager reads `triager/workflow-mapping.yaml` to decide which workflow function(s) to call for each incoming request type:

| Request Type | Workflows |
|---|---|
| Suggest Dataset for GDEX | `cost_summary` |
| Submit Your Data to GDEX | `cost_summary`, `dda_response` |
| Request for a proposal data management plan and budget | `cost_summary`, `switch_status` |
| General Data Help, Dataset Questions, Web Site Problems, Web Services & APIs, Data Download Problem | `ticket_assignment`, `ticket_priority` |

---

## Secrets Required

| Secret | Used By |
|---|---|
| `PROD_JIRA_API_TOKEN` | Both workflows — authenticates against the Jira REST API |
| `GOOGLE_CREDENTIALS` | Scheduled + event workflows — Google OAuth client config |
| `GOOGLE_TOKEN` | Scheduled + event workflows — Google OAuth token |

Secrets are managed in the `GDEX_JIRA_PRODUCTION_ENV` GitHub Actions environment.

---

## Requirements

- Python 3.11
- Dependencies listed in `requirements.txt`


