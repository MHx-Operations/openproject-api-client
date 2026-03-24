# openproject-api-client

Python client and CLI for the OpenProject API v3. Read and write access to projects, work packages,
relations, versions, users, memberships, statuses, grids, and queries.

API documentation: https://www.openproject.org/docs/api/

## Installation

```bash
pip install git+https://github.com/MHx-Operations/openproject-api-client.git#egg=openproject_api_client
```

## Quick Start (Python)

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

# create a new work package
new_wp = client.create_workpackage(
    project_id=1, subject="Implement feature X",
    type_id=1, assignee_id=3, priority_id=2,
)

# update status of a work package
client.update_workpackage(new_wp.id, lock_version=new_wp.lockversion, status_id=7)

# add a comment
client.add_workpackage_comment(new_wp.id, "Done with implementation")

# create a relation
client.create_relation(from_id=42, to_id=50, relation_type="blocks")
```

## Quick Start (CLI)

```bash
export OPENPROJECT_BASEURL="https://openproject.example.com/"
export OPENPROJECT_APIKEY="your-api-key"

# show full usage guide (for humans and AI agents)
openproject-cli guide

# read
openproject-cli --json projects
openproject-cli --json work-packages --project-id 5 --status open
openproject-cli --json statuses
openproject-cli --json users

# write
openproject-cli create-work-package --project-id 1 --subject "New task" --assignee-id 3
openproject-cli update-work-package 42 --status-id 7
openproject-cli add-comment 42 --message "Status update: done"
openproject-cli create-relation --from-id 42 --to-id 50 --type blocks
```

Use `openproject-cli guide` for the full reference including AI-agent workflow.

## Read Methods

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

## Write Methods

| Method | Description |
|--------|-------------|
| `create_workpackage(project_id, subject, ...)` | Create a new work package |
| `update_workpackage(id, lock_version, ...)` | Update a work package (optimistic locking) |
| `add_workpackage_comment(id, message)` | Add a comment/activity to a work package |
| `create_relation(from_id, to_id, type, ...)` | Create a relation between work packages |
| `post(resource, body)` | Generic POST for any API v3 endpoint |
| `patch(resource, body)` | Generic PATCH for any API v3 endpoint |

## CLI Commands

### Read Commands

```
openproject-cli projects                            List all projects
openproject-cli work-packages [--status open|closed|all] [--project-id N] [--query-id N]
openproject-cli work-package <id>                   Get single work package
openproject-cli statuses                            List all statuses (useful for ID lookup)
openproject-cli users                               List all users
openproject-cli versions                            List all versions
openproject-cli relations                           List all relations
openproject-cli memberships                         List all memberships
openproject-cli grids [--scope ...]                 List all grids
openproject-cli placeholder-users                   List placeholder users
openproject-cli relation|version|user|placeholder-user|membership|status|grid|query <id>
```

### Write Commands

```
openproject-cli create-work-package --project-id N --subject "..." [options]
openproject-cli update-work-package <id> [--subject "..."] [--status-id N] [options]
openproject-cli add-comment <id> --message "..."
openproject-cli create-relation --from-id N --to-id N --type <relation-type> [options]
```

### Options

- `--json` — Machine-parseable JSON output (recommended for scripts and AI agents)
- `--baseurl URL` — Override env OPENPROJECT_BASEURL
- `--apikey KEY` — Override env OPENPROJECT_APIKEY
- `guide` — Full usage guide (no credentials needed)

## API Coverage

### Supported (Read & Write)

| Resource | List | Get | Create | Update | Filter | Notes |
|----------|:----:|:---:|:------:|:------:|:------:|-------|
| Projects | :white_check_mark: | :white_check_mark: | — | — | — | Hierarchy paths via `get_projects_dict()` |
| Work Packages | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | status, project, query | Embedded relations on single fetch |
| Relations | :white_check_mark: | :white_check_mark: | :white_check_mark: | — | — | Directed (from → to), with lag |
| Activities | — | — | :white_check_mark: | — | — | Add comments to work packages |
| Versions | :white_check_mark: | :white_check_mark: | — | — | — | Milestones |
| Users | :white_check_mark: | :white_check_mark: | — | — | — | |
| Placeholder Users | :white_check_mark: | :white_check_mark: | — | — | — | |
| Memberships | :white_check_mark: | :white_check_mark: | — | — | — | Project memberships with roles |
| Statuses | :white_check_mark: | :white_check_mark: | — | — | — | Work package statuses |
| Grids | :white_check_mark: | :white_check_mark: | — | — | scope | Boards / dashboards with widgets |
| Queries | — | :white_check_mark: | — | — | — | Saved query with embedded results |

### Not yet supported

| Resource | API Operations | Priority | Notes |
|----------|---------------|----------|-------|
| Types | GET | High | Work package types (Task, Bug, etc.) — needed for type ID lookup |
| Priorities | GET | High | Priority levels — needed for priority ID lookup |
| Time Entries | GET, POST, PATCH, DELETE | High | Time tracking |
| Attachments | GET, POST, DELETE | Medium | File attachments |
| Categories | GET | Medium | Work package categories |
| Budgets | GET | Medium | Project budgets |
| Notifications | GET, PATCH | Medium | In-app notifications |
| Activities | GET | Medium | Read work package journal/history |
| Custom Actions | GET, PATCH, DELETE, Execute | Low | Custom workflow actions |
| Custom Fields / Options | GET, PATCH, DELETE | Low | Custom field definitions |
| Days / Work Schedule | GET, PATCH | Low | Working/non-working days |
| Documents | GET | Low | Project documents |
| File Links | GET, PATCH, DELETE | Low | External storage links |
| Groups | GET, POST, PATCH, DELETE | Low | User groups |
| Help Texts | GET | Low | Attribute help texts |
| Meetings | GET | Low | Meeting resources |
| News | GET | Low | Project news |
| OAuth | GET, POST, DELETE | Low | OAuth applications/credentials |
| Portfolios | GET, POST, PATCH, DELETE | Low | Project portfolios |
| Posts | GET | Low | Forum posts |
| Principals | GET | Low | Users, groups, placeholder users |
| Programs | GET, POST, PATCH, DELETE | Low | Programs |
| Project Storages | GET, POST, PATCH, DELETE | Low | Project ↔ storage links |
| Reminders | GET, POST, DELETE | Low | Work package reminders |
| Rendering | POST | Low | Markdown/plain text rendering |
| Revisions | GET | Low | SCM revisions |
| Roles | GET | Low | Permission roles |
| Storages | GET, POST, PATCH, DELETE | Low | External file storages (Nextcloud, etc.) |
| Views | GET, PATCH, DELETE | Low | Saved views |
| Wiki Pages | GET, PATCH, DELETE | Low | Wiki content |
| Workspaces | GET | Low | Projects (OpenProject 17+) |

### Still missing for full write workflow

- **DELETE** operations (work packages, relations, etc.)
- **Types endpoint** (GET) — for looking up type IDs when creating work packages
- **Priorities endpoint** (GET) — for looking up priority IDs
- **Time Entries** — for time tracking workflows

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
