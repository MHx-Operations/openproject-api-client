# openproject-api-client

Python client for the OpenProject API v3. Read-only access to projects, work packages,
relations, versions, users, memberships, statuses, grids, and queries.

API documentation: https://www.openproject.org/docs/api/

## Installation

```bash
pip install git+https://github.com/MHx-Operations/openproject-api-client.git#egg=openproject_api_client
```

## Quick Start

```python
from openproject_api_client import ApiClient

client = ApiClient("https://openproject.example.com/", "your-api-key")

# list all projects
for project in client.get_projects():
    print(project)

# fetch open work packages for a specific project
work_packages = client.get_workpackages_by_project_id(46, status='open')

# fetch a single work package with embedded relations
wp = client.get_workpackage(1155)
print(wp.relations_in, wp.relations_out)

# fetch work packages from a saved query
wps = client.get_workpackages_by_query_id(12)
```

## Available Methods

| Method | Description |
|--------|-------------|
| `get_projects()` | All projects as list |
| `get_projects_dict()` | All projects as dict (keyed by ID, with hierarchy paths) |
| `get_workpackage(id)` | Single work package by ID |
| `get_workpackages(status, status_ids)` | All work packages, optionally filtered |
| `get_workpackages_by_project_id(id, status)` | Work packages for a specific project |
| `get_workpackages_by_query_id(id)` | Work packages from a saved query |
| `get_relation(id)` / `get_relations()` | Relations between work packages |
| `get_version(id)` / `get_versions()` | Project versions (milestones) |
| `get_user(id)` / `get_users()` | User accounts |
| `get_placeholder_user(id)` / `get_placeholder_users()` | Placeholder users |
| `get_project_member(id)` / `get_project_members()` | Project memberships |
| `get_status(id)` / `get_statuses()` | Work package statuses |
| `get_grid(id)` / `get_grids(scope)` | Dashboard grids (boards) |
| `get_query(id)` | Saved query definition |
| `get(resource, payload)` | Generic GET for any API v3 endpoint |

## API Coverage

This client currently provides **read-only** access to a subset of the OpenProject API v3.
The table below shows all resource types available in the API and their support status.

### Supported

| Resource | List | Get | Filter | Notes |
|----------|:----:|:---:|:------:|-------|
| Projects | :white_check_mark: | :white_check_mark: | — | Hierarchy paths via `get_projects_dict()` |
| Work Packages | :white_check_mark: | :white_check_mark: | status, project, query | Embedded relations on single fetch |
| Relations | :white_check_mark: | :white_check_mark: | — | Directed (from → to) |
| Versions | :white_check_mark: | :white_check_mark: | — | Milestones |
| Users | :white_check_mark: | :white_check_mark: | — | |
| Placeholder Users | :white_check_mark: | :white_check_mark: | — | |
| Memberships | :white_check_mark: | :white_check_mark: | — | Project memberships |
| Statuses | :white_check_mark: | :white_check_mark: | — | Work package statuses |
| Grids | :white_check_mark: | :white_check_mark: | scope | Boards / dashboards with widgets |
| Queries | — | :white_check_mark: | — | Saved query with embedded results |

### Not yet supported

| Resource | API Operations | Notes |
|----------|---------------|-------|
| Activities | GET | Work package journal entries |
| Actions / Capabilities | GET | Permission system |
| Attachments | GET, POST, DELETE | File attachments |
| Budgets | GET | Project budgets |
| Categories | GET | Work package categories |
| Custom Actions | GET, PATCH, DELETE, Execute | Custom workflow actions |
| Custom Fields / Options | GET, PATCH, DELETE | Custom field definitions |
| Days / Work Schedule | GET, PATCH | Working/non-working days |
| Documents | GET | Project documents |
| File Links | GET, PATCH, DELETE | External storage links |
| Groups | GET, POST, PATCH, DELETE | User groups |
| Help Texts | GET | Attribute help texts |
| Meetings | GET | Meeting resources |
| News | GET | Project news |
| Notifications | GET, PATCH | In-app notifications |
| OAuth | GET, POST, DELETE | OAuth applications/credentials |
| Portfolios | GET, POST, PATCH, DELETE | Project portfolios |
| Posts | GET | Forum posts |
| Principals | GET | Users, groups, placeholder users |
| Priorities | GET | Work package priorities |
| Programs | GET, POST, PATCH, DELETE | Programs |
| Project Storages | GET, POST, PATCH, DELETE | Project ↔ storage links |
| Reminders | GET, POST, DELETE | Work package reminders |
| Rendering | POST | Markdown/plain text rendering |
| Revisions | GET | SCM revisions |
| Roles | GET | Permission roles |
| Storages | GET, POST, PATCH, DELETE | External file storages (Nextcloud, etc.) |
| Time Entries | GET, POST, PATCH, DELETE | Time tracking |
| Types | GET | Work package types (Task, Bug, etc.) |
| Views | GET, PATCH, DELETE | Saved views |
| Wiki Pages | GET, PATCH, DELETE | Wiki content |
| Workspaces | GET | Projects (OpenProject 17+) |

> **Note:** Write operations (POST, PATCH, DELETE) are listed for the API but this client
> is currently read-only. The `get()` method can be used to access any GET endpoint not
> listed above.

## OpenProject Compatibility

Works with **OpenProject 10 and later**. Uses the stable API v3 (`/api/v3/`).

### Notes for specific versions

- **OpenProject 14+**: The Relations API renamed the `delay` attribute to `lag`.
  This client exposes the field as returned by the API, so the attribute name
  depends on your OpenProject version.

- **OpenProject 17+**: Introduces the Workspaces concept. Project-scoped endpoints
  like `/api/v3/projects/{id}/work_packages` are deprecated in favor of
  `/api/v3/workspaces/{id}/work_packages`. The old endpoints still work but may
  be removed in a future version.

## Requirements

- Python >= 3.9
- requests >= 2.25.1

## License

MIT
