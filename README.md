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
