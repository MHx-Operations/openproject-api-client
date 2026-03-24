# openproject-api-client

Python client and CLI for the OpenProject API v3. Full read/write/delete access to projects,
work packages, relations, time entries, notifications, and more.

API documentation: https://www.openproject.org/docs/api/

## Installation

```bash
pip install git+https://github.com/MHx-Operations/openproject-api-client.git#egg=openproject_api_client
```

## Quick Start (Python)

```python
from openproject_api_client import ApiClient

client = ApiClient("https://openproject.example.com/", "your-api-key")

# discover available types and priorities
types = client.get_types()           # [Type(1): Task, Type(2): Bug, ...]
priorities = client.get_priorities() # [Priority(1): Low, Priority(2): High, ...]

# list all projects
for project in client.get_projects():
    print(project)

# fetch open work packages for a project
work_packages = client.get_workpackages_by_project_id(46, status='open')

# create a new work package
new_wp = client.create_workpackage(
    project_id=1, subject="Implement feature X",
    type_id=1, assignee_id=3, priority_id=2,
)

# update status
client.update_workpackage(new_wp.id, lock_version=new_wp.lockversion, status_id=7)

# add a comment
client.add_workpackage_comment(new_wp.id, "Done with implementation")

# log time
client.create_time_entry(new_wp.id, hours="PT2H", spent_on="2024-03-15")

# create a relation
client.create_relation(from_id=42, to_id=50, relation_type="blocks")

# delete
client.delete_workpackage(99)
client.delete_relation(100)
```

## Quick Start (CLI)

```bash
export OPENPROJECT_BASEURL="https://openproject.example.com/"
export OPENPROJECT_APIKEY="your-api-key"

# show full usage guide (for humans and AI agents)
openproject-cli guide

# read
openproject-cli --json projects
openproject-cli --json types
openproject-cli --json priorities
openproject-cli --json statuses
openproject-cli --json work-packages --project-id 5 --status open
openproject-cli --json time-entries --work-package-id 42

# write
openproject-cli create-work-package --project-id 1 --subject "New task" --type-id 1
openproject-cli update-work-package 42 --status-id 7
openproject-cli add-comment 42 --message "Status update: done"
openproject-cli create-time-entry --work-package-id 42 --hours PT2H --spent-on 2024-03-15
openproject-cli create-relation --from-id 42 --to-id 50 --type blocks
openproject-cli mark-notification-read 55

# delete
openproject-cli delete-work-package 99
openproject-cli delete-relation 100
openproject-cli delete-time-entry 55
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
| `get_type(id)` / `get_types()` | Work package types (Task, Bug, etc.) |
| `get_types_by_project_id(id)` | Types available in a specific project |
| `get_priority(id)` / `get_priorities()` | Priority levels |
| `get_category(id)` / `get_categories_by_project_id(id)` | Work package categories |
| `get_relation(id)` / `get_relations()` | Relations between work packages |
| `get_version(id)` / `get_versions()` | Project versions (milestones) |
| `get_user(id)` / `get_users()` | User accounts |
| `get_placeholder_user(id)` / `get_placeholder_users()` | Placeholder users |
| `get_project_member(id)` / `get_project_members()` | Project memberships |
| `get_status(id)` / `get_statuses()` | Work package statuses |
| `get_time_entry(id)` / `get_time_entries(wp_id, project_id)` | Time tracking entries |
| `get_activities(wp_id)` | Work package activities/journal |
| `get_attachment(id)` / `get_attachments_by_work_package(wp_id)` | File attachments |
| `get_notification(id)` / `get_notifications()` | In-app notifications |
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
| `create_time_entry(wp_id, hours, spent_on, ...)` | Log time on a work package |
| `update_time_entry(id, lock_version, ...)` | Update a time entry |
| `mark_notification_read(id)` | Mark notification as read |
| `mark_notification_unread(id)` | Mark notification as unread |
| `mark_all_notifications_read()` | Mark all notifications as read |
| `post(resource, body)` | Generic POST for any API v3 endpoint |
| `patch(resource, body)` | Generic PATCH for any API v3 endpoint |

## Delete Methods

| Method | Description |
|--------|-------------|
| `delete_workpackage(id)` | Delete a work package |
| `delete_relation(id)` | Delete a relation |
| `delete_time_entry(id)` | Delete a time entry |
| `delete_attachment(id)` | Delete an attachment |
| `delete(resource)` | Generic DELETE for any API v3 endpoint |

## API Coverage

### Supported (Read / Write / Delete)

| Resource | List | Get | Create | Update | Delete | Filter | Notes |
|----------|:----:|:---:|:------:|:------:|:------:|:------:|-------|
| Projects | :white_check_mark: | :white_check_mark: | — | — | — | — | Hierarchy paths via `get_projects_dict()` |
| Work Packages | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | status, project, query | Embedded relations on single fetch |
| Relations | :white_check_mark: | :white_check_mark: | :white_check_mark: | — | :white_check_mark: | — | Directed (from → to), with lag |
| Types | :white_check_mark: | :white_check_mark: | — | — | — | project | Work package types (Task, Bug, etc.) |
| Priorities | :white_check_mark: | :white_check_mark: | — | — | — | — | Priority levels |
| Categories | :white_check_mark: | :white_check_mark: | — | — | — | project | Work package categories |
| Time Entries | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | wp, project | Time tracking |
| Activities | :white_check_mark: | — | :white_check_mark: | — | — | wp | Comments / journal entries |
| Attachments | :white_check_mark: | :white_check_mark: | — | — | :white_check_mark: | wp | File attachments |
| Notifications | :white_check_mark: | :white_check_mark: | — | :white_check_mark: | — | — | Read/unread state |
| Versions | :white_check_mark: | :white_check_mark: | — | — | — | — | Milestones |
| Users | :white_check_mark: | :white_check_mark: | — | — | — | — | |
| Placeholder Users | :white_check_mark: | :white_check_mark: | — | — | — | — | |
| Memberships | :white_check_mark: | :white_check_mark: | — | — | — | — | With roles |
| Statuses | :white_check_mark: | :white_check_mark: | — | — | — | — | |
| Grids | :white_check_mark: | :white_check_mark: | — | — | — | scope | Boards / dashboards |
| Queries | — | :white_check_mark: | — | — | — | — | Saved queries |

### Not yet supported

| Resource | Priority | Notes |
|----------|----------|-------|
| Budgets | Medium | Project budgets |
| Custom Actions | Low | Custom workflow actions |
| Custom Fields / Options | Low | Custom field definitions |
| Days / Work Schedule | Low | Working/non-working days |
| Documents | Low | Project documents |
| File Links | Low | External storage links |
| Groups | Low | User groups |
| Help Texts | Low | Attribute help texts |
| Meetings | Low | Meeting resources |
| News | Low | Project news |
| OAuth | Low | OAuth applications/credentials |
| Portfolios | Low | Project portfolios |
| Posts | Low | Forum posts |
| Principals | Low | Users, groups, placeholder users |
| Programs | Low | Programs |
| Project Storages | Low | Project ↔ storage links |
| Reminders | Low | Work package reminders |
| Rendering | Low | Markdown/plain text rendering |
| Revisions | Low | SCM revisions |
| Roles | Low | Permission roles |
| Storages | Low | External file storages |
| Views | Low | Saved views |
| Wiki Pages | Low | Wiki content |
| Workspaces | Low | Projects (OpenProject 17+) |

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
