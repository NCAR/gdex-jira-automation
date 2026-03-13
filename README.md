# gdex-jira-automation

This repository contains automation for handling Jira tickets using GitHub Actions. It includes event-driven and scheduled workflows to process Jira tickets based on various triggers.

## Directory Structure

- **`.github/workflows/`**: Contains GitHub Actions workflow YAML files.
  - **`jira_event.yml`**: Event-driven workflow triggered by Jira tickets.
  - **`scheduled_jobs.yml`**: Cron-based workflow for time-driven tasks.

- **`entrypoints/`**: Scripts triggered by workflows.
  - **`run_event.py`**: Handles event-driven Jira tickets.
  - **`run_scheduled.py`**: Executes scheduled tasks (cron jobs).

- **`triager/`**: Decides which workflow to run based on ticket type.
  - **`triager.py`**: Logic to choose the correct handler based on the ticket.
  - **`workflow_mapping.yaml`**: Maps request types to workflow handlers.

- **`workflows/`**: Contains the actual workflow logic.
  - **`event/`**: Handles event-driven workflows (e.g., ticket assignment, curation responses).
  - **`scheduled/`**: Handles scheduled workflows (e.g., stale ticket checker, clean sweep).

- **`jira/`**: Jira-specific logic (API operations).
  - **`helpers.py`**: Encapsulates Jira API calls for querying, assigning, and updating tickets.

- **`utils/`**: Shared utilities for the automation.
  - **`logger.py`**: Central logging for all workflows.
  - **`config_loader.py`**: Loads configuration and environment variables.

- **`tests/`**: Unit and integration tests for the automation.

## How It Works

1. **Event-Driven**: Triggered when Jira sends a new ticket. `run_event.py` processes the ticket and triggers the correct workflow (assignment, curation).
2. **Scheduled Jobs**: Triggered by cron (e.g., `jira_clean_sweep.py` checks unassigned tickets).
3. **Triager**: Decides which workflow to call based on the ticket type.

## Requirements

- Python 3.x
- Dependencies listed in `requirements.txt`

---
---
