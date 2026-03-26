import argparse
import os
import json
import sys
import textwrap

import openproject_api_client as opc

GUIDE_TEXT = textwrap.dedent("""\
openproject-cli — Command-line interface for OpenProject API v3

SETUP
  export OPENPROJECT_BASEURL="https://your-instance.openproject.com/"
  export OPENPROJECT_APIKEY="your-api-key"

  Alternatively pass --baseurl and --apikey as arguments.

OUTPUT
  Default output is human-readable text (one line per resource).
  Use --json for machine-parseable JSON output (recommended for scripts).

READ COMMANDS
  openproject-cli get-projects                          List all projects (with hierarchy)
  openproject-cli get-work-packages                     List all work packages (default: all)
  openproject-cli get-work-packages --status open       Filter by status: all, open, closed
  openproject-cli get-work-packages --project-id 5      Filter by project
  openproject-cli get-work-packages --query-id 99       Use a saved query
  openproject-cli get-work-package 42                   Get single work package by ID
  openproject-cli get-types                             List all work package types
  openproject-cli get-types --project-id 5              Types available in a project
  openproject-cli get-priorities                        List all priorities
  openproject-cli get-statuses                          List all statuses (get IDs for updates)
  openproject-cli get-categories --project-id 5         List categories for a project
  openproject-cli get-users                             List all users (get IDs for assignments)
  openproject-cli get-versions                          List all versions/milestones
  openproject-cli get-relations                         List all relations
  openproject-cli get-memberships                       List all project memberships
  openproject-cli get-time-entries                      List all time entries
  openproject-cli get-time-entries --work-package-id 42 Filter by work package
  openproject-cli get-time-entries --project-id 5       Filter by project
  openproject-cli get-activities 42                     List activities for a work package
  openproject-cli get-attachments 42                    List attachments for a work package
  openproject-cli get-notifications                     List notifications
  openproject-cli get-grids                             List all grids/boards
  openproject-cli get-grids --scope /projects/1/boards  Filter grids by scope
  openproject-cli get-placeholder-users                 List placeholder users

  Single-resource: get-relation, get-version, get-user, get-placeholder-user, get-membership,
                   get-status, get-grid, get-query, get-type, get-priority, get-category,
                   get-time-entry, get-attachment, get-notification

WRITE COMMANDS
  openproject-cli create-work-package --project-id 1 --subject "Title" \\
      [--type-id N] [--status-id N] [--assignee-id N] [--responsible-id N] \\
      [--priority-id N] [--version-id N] [--parent-id N] [--category-id N] \\
      [--budget-id N] [--start-date YYYY-MM-DD] [--due-date YYYY-MM-DD] \\
      [--estimated-time PT8H] [--percentage-done 50] \\
      [--description "markdown text"] [--schedule-manually]

  openproject-cli update-work-package 42 \\
      [--subject "New title"] [--status-id N] [--assignee-id N] ...
      Note: lock-version is fetched automatically.

  openproject-cli add-comment 42 --message "Status update: done with testing"

  openproject-cli create-relation --from-id 42 --to-id 50 --type blocks \\
      [--description "reason"] [--lag 2]

  openproject-cli create-time-entry --work-package-id 42 --hours PT2H \\
      --spent-on 2024-03-15 [--activity-id N] [--comment "text"]

  openproject-cli update-time-entry 100 \\
      [--hours PT3H] [--spent-on 2024-03-16] [--comment "text"]

  openproject-cli mark-notification-read 55
  openproject-cli mark-notification-unread 55
  openproject-cli mark-all-notifications-read

DELETE COMMANDS
  openproject-cli delete-work-package 42
  openproject-cli delete-relation 100
  openproject-cli delete-time-entry 55
  openproject-cli delete-attachment 33

TYPICAL AI-AGENT WORKFLOW
  1. Discover context:
     openproject-cli --json get-types              # get type IDs (Task, Bug, ...)
     openproject-cli --json get-priorities          # get priority IDs
     openproject-cli --json get-statuses            # get status IDs
     openproject-cli --json get-users               # get user IDs
     openproject-cli --json get-projects            # get project IDs

  2. Read work packages:
     openproject-cli --json get-work-packages --project-id 5 --status open

  3. Update status:
     openproject-cli --json update-work-package 42 --status-id 7

  4. Add comment:
     openproject-cli add-comment 42 --message "Implemented feature X"

  5. Create new work package:
     openproject-cli --json create-work-package --project-id 5 \\
         --subject "Implement Y" --type-id 1 --assignee-id 3

  6. Log time:
     openproject-cli --json create-time-entry --work-package-id 42 \\
         --hours PT2H --spent-on 2024-03-15

  7. Create relation:
     openproject-cli create-relation --from-id 42 --to-id 50 --type blocks

RELATION TYPES
  relates, duplicates, duplicated, blocks, blocked,
  precedes, follows, includes, partof, requires, required

TIME FORMAT
  ISO 8601 duration: PT1H (1 hour), PT30M (30 min), P1D (1 day), PT8H (8 hours)

EXIT CODES
  0  Success
  1  API error or request failure
  2  Deleted successfully (delete commands, text mode)
""")


def main():
    parser = argparse.ArgumentParser(
        description='openproject-cli — CLI for OpenProject API v3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--apikey', help='API key (or env OPENPROJECT_APIKEY)', metavar='KEY',
                        dest='apikey', required=False)
    parser.add_argument('--baseurl', help='base URL (or env OPENPROJECT_BASEURL)', metavar='URL',
                        dest='baseurl', required=False)
    parser.add_argument('--json', help='output as JSON (recommended for scripts)',
                        action='store_true', dest='json')

    subparsers = parser.add_subparsers(dest='mode')

    # -- guide -------------------------------------------------------------
    subparsers.add_parser('guide', help='show full usage guide for humans and AI agents')

    # -- read commands -----------------------------------------------------

    subparsers.add_parser('get-projects', help='list all projects')

    sp_wp = subparsers.add_parser('get-work-packages', help='list work packages')
    sp_wp.add_argument('--project-id', type=int, help='filter by project id')
    sp_wp.add_argument('--query-id', type=int, help='fetch by saved query id')
    sp_wp.add_argument('--status', choices=['all', 'open', 'closed'], default=None,
                       help='filter by status')

    sp_wp_single = subparsers.add_parser('get-work-package', help='get a single work package')
    sp_wp_single.add_argument('id', type=int, help='work package id')

    sp_types = subparsers.add_parser('get-types', help='list all work package types')
    sp_types.add_argument('--project-id', type=int, help='filter by project id')

    sp_type = subparsers.add_parser('get-type', help='get a single type')
    sp_type.add_argument('id', type=int, help='type id')

    subparsers.add_parser('get-priorities', help='list all priorities')

    sp_priority = subparsers.add_parser('get-priority', help='get a single priority')
    sp_priority.add_argument('id', type=int, help='priority id')

    sp_categories = subparsers.add_parser('get-categories', help='list categories for a project')
    sp_categories.add_argument('--project-id', type=int, required=True, help='project id')

    sp_category = subparsers.add_parser('get-category', help='get a single category')
    sp_category.add_argument('id', type=int, help='category id')

    subparsers.add_parser('get-relations', help='list all relations')

    sp_relation = subparsers.add_parser('get-relation', help='get a single relation')
    sp_relation.add_argument('id', type=int, help='relation id')

    subparsers.add_parser('get-versions', help='list all versions')

    sp_version = subparsers.add_parser('get-version', help='get a single version')
    sp_version.add_argument('id', type=int, help='version id')

    subparsers.add_parser('get-users', help='list all users')

    sp_user = subparsers.add_parser('get-user', help='get a single user')
    sp_user.add_argument('id', type=int, help='user id')

    subparsers.add_parser('get-placeholder-users', help='list all placeholder users')

    sp_ph_user = subparsers.add_parser('get-placeholder-user', help='get a single placeholder user')
    sp_ph_user.add_argument('id', type=int, help='placeholder user id')

    subparsers.add_parser('get-memberships', help='list all memberships')

    sp_member = subparsers.add_parser('get-membership', help='get a single membership')
    sp_member.add_argument('id', type=int, help='membership id')

    subparsers.add_parser('get-statuses', help='list all statuses')

    sp_status = subparsers.add_parser('get-status', help='get a single status')
    sp_status.add_argument('id', type=int, help='status id')

    sp_time_entries = subparsers.add_parser('get-time-entries', help='list time entries')
    sp_time_entries.add_argument('--work-package-id', type=int, help='filter by work package')
    sp_time_entries.add_argument('--project-id', type=int, help='filter by project')

    sp_time_entry = subparsers.add_parser('get-time-entry', help='get a single time entry')
    sp_time_entry.add_argument('id', type=int, help='time entry id')

    sp_activities = subparsers.add_parser('get-activities', help='list activities for a work package')
    sp_activities.add_argument('id', type=int, help='work package id')

    sp_attachments = subparsers.add_parser('get-attachments', help='list attachments for a work package')
    sp_attachments.add_argument('id', type=int, help='work package id')

    sp_attachment = subparsers.add_parser('get-attachment', help='get a single attachment')
    sp_attachment.add_argument('id', type=int, help='attachment id')

    subparsers.add_parser('get-notifications', help='list notifications')

    sp_notification = subparsers.add_parser('get-notification', help='get a single notification')
    sp_notification.add_argument('id', type=int, help='notification id')

    sp_grids = subparsers.add_parser('get-grids', help='list all grids')
    sp_grids.add_argument('--scope', help='filter by scope')

    sp_grid = subparsers.add_parser('get-grid', help='get a single grid')
    sp_grid.add_argument('id', type=int, help='grid id')

    sp_query = subparsers.add_parser('get-query', help='get a single query')
    sp_query.add_argument('id', type=int, help='query id')

    # -- write commands ----------------------------------------------------

    sp_create_wp = subparsers.add_parser('create-work-package', help='create a new work package')
    sp_create_wp.add_argument('--project-id', type=int, required=True, help='project id')
    sp_create_wp.add_argument('--subject', required=True, help='work package title')
    sp_create_wp.add_argument('--type-id', type=int, help='type id')
    sp_create_wp.add_argument('--status-id', type=int, help='status id')
    sp_create_wp.add_argument('--assignee-id', type=int, help='assignee user id')
    sp_create_wp.add_argument('--responsible-id', type=int, help='responsible user id')
    sp_create_wp.add_argument('--priority-id', type=int, help='priority id')
    sp_create_wp.add_argument('--version-id', type=int, help='version id')
    sp_create_wp.add_argument('--parent-id', type=int, help='parent work package id')
    sp_create_wp.add_argument('--category-id', type=int, help='category id')
    sp_create_wp.add_argument('--budget-id', type=int, help='budget id')
    sp_create_wp.add_argument('--start-date', help='start date (YYYY-MM-DD)')
    sp_create_wp.add_argument('--due-date', help='due date (YYYY-MM-DD)')
    sp_create_wp.add_argument('--estimated-time', help='estimated time (e.g. PT8H)')
    sp_create_wp.add_argument('--percentage-done', type=int, help='progress 0-100')
    sp_create_wp.add_argument('--description', help='description (markdown)')
    sp_create_wp.add_argument('--schedule-manually', action='store_true', default=None,
                              help='schedule manually')

    sp_update_wp = subparsers.add_parser('update-work-package', help='update a work package')
    sp_update_wp.add_argument('id', type=int, help='work package id')
    sp_update_wp.add_argument('--subject', help='new subject')
    sp_update_wp.add_argument('--type-id', type=int, help='type id')
    sp_update_wp.add_argument('--status-id', type=int, help='status id')
    sp_update_wp.add_argument('--assignee-id', type=int, help='assignee user id')
    sp_update_wp.add_argument('--responsible-id', type=int, help='responsible user id')
    sp_update_wp.add_argument('--priority-id', type=int, help='priority id')
    sp_update_wp.add_argument('--version-id', type=int, help='version id')
    sp_update_wp.add_argument('--parent-id', type=int, help='parent work package id')
    sp_update_wp.add_argument('--category-id', type=int, help='category id')
    sp_update_wp.add_argument('--budget-id', type=int, help='budget id')
    sp_update_wp.add_argument('--start-date', help='start date (YYYY-MM-DD)')
    sp_update_wp.add_argument('--due-date', help='due date (YYYY-MM-DD)')
    sp_update_wp.add_argument('--estimated-time', help='estimated time (e.g. PT8H)')
    sp_update_wp.add_argument('--remaining-time', help='remaining time (e.g. PT2H)')
    sp_update_wp.add_argument('--percentage-done', type=int, help='progress 0-100')
    sp_update_wp.add_argument('--description', help='description (markdown)')
    sp_update_wp.add_argument('--schedule-manually', action='store_true', default=None,
                              help='schedule manually')

    sp_comment = subparsers.add_parser('add-comment', help='add a comment to a work package')
    sp_comment.add_argument('id', type=int, help='work package id')
    sp_comment.add_argument('--message', required=True, help='comment text (markdown)')

    sp_create_rel = subparsers.add_parser('create-relation', help='create a relation')
    sp_create_rel.add_argument('--from-id', type=int, required=True, help='source work package id')
    sp_create_rel.add_argument('--to-id', type=int, required=True, help='target work package id')
    sp_create_rel.add_argument('--type', required=True, dest='relation_type',
                               choices=['relates', 'duplicates', 'duplicated', 'blocks', 'blocked',
                                        'precedes', 'follows', 'includes', 'partof', 'requires', 'required'],
                               help='relation type')
    sp_create_rel.add_argument('--description', help='relation description')
    sp_create_rel.add_argument('--lag', type=int, help='lag in days (for precedes/follows)')

    sp_create_te = subparsers.add_parser('create-time-entry', help='create a time entry')
    sp_create_te.add_argument('--work-package-id', type=int, required=True, help='work package id')
    sp_create_te.add_argument('--hours', required=True, help='hours (e.g. PT2H, PT30M)')
    sp_create_te.add_argument('--spent-on', required=True, help='date (YYYY-MM-DD)')
    sp_create_te.add_argument('--activity-id', type=int, help='time entry activity id')
    sp_create_te.add_argument('--comment', help='comment')
    sp_create_te.add_argument('--project-id', type=int, help='project id')

    sp_update_te = subparsers.add_parser('update-time-entry', help='update a time entry')
    sp_update_te.add_argument('id', type=int, help='time entry id')
    sp_update_te.add_argument('--hours', help='hours (e.g. PT2H)')
    sp_update_te.add_argument('--spent-on', help='date (YYYY-MM-DD)')
    sp_update_te.add_argument('--activity-id', type=int, help='time entry activity id')
    sp_update_te.add_argument('--comment', help='comment')

    sp_notif_read = subparsers.add_parser('mark-notification-read', help='mark notification as read')
    sp_notif_read.add_argument('id', type=int, help='notification id')

    sp_notif_unread = subparsers.add_parser('mark-notification-unread', help='mark notification as unread')
    sp_notif_unread.add_argument('id', type=int, help='notification id')

    subparsers.add_parser('mark-all-notifications-read', help='mark all notifications as read')

    # -- delete commands ---------------------------------------------------

    sp_del_wp = subparsers.add_parser('delete-work-package', help='delete a work package')
    sp_del_wp.add_argument('id', type=int, help='work package id')

    sp_del_rel = subparsers.add_parser('delete-relation', help='delete a relation')
    sp_del_rel.add_argument('id', type=int, help='relation id')

    sp_del_te = subparsers.add_parser('delete-time-entry', help='delete a time entry')
    sp_del_te.add_argument('id', type=int, help='time entry id')

    sp_del_att = subparsers.add_parser('delete-attachment', help='delete an attachment')
    sp_del_att.add_argument('id', type=int, help='attachment id')

    args = parser.parse_args()

    # guide does not need credentials
    if args.mode == 'guide':
        print(GUIDE_TEXT)
        return

    # get OPENPROJECT_BASEURL from cli arg or environment
    baseurl = args.baseurl
    if not baseurl:
        baseurl = os.environ.get('OPENPROJECT_BASEURL')

    if not baseurl:
        raise Exception('specify base url with env:OPENPROJECT_BASEURL or by --baseurl argument')

    # get OPENPROJECT_APIKEY from cli arg or environment
    apikey = args.apikey
    if not apikey:
        apikey = os.environ.get('OPENPROJECT_APIKEY')

    if not apikey:
        raise Exception('specify API key with env:OPENPROJECT_APIKEY or by --apikey argument')

    client = opc.ApiClient(baseurl, apikey)

    try:
        result = dispatch(client, args)
        if result is True:
            # delete operations return True
            if args.json:
                print(json.dumps({"deleted": True}))
            else:
                print("deleted")
        elif result is not None:
            if args.json:
                json_out(result)
            else:
                text_out(result)

    except (opc.ApiError, opc.RequestError) as err:
        print(f"error: {err}", file=sys.stderr)
        sys.exit(1)


def dispatch(client, args):
    """Route the parsed CLI args to the right client method."""
    mode = args.mode

    # read commands
    if mode == 'get-projects':
        return client.get_projects()

    elif mode == 'get-work-packages':
        if args.query_id:
            return client.get_workpackages_by_query_id(args.query_id)
        elif args.project_id:
            return client.get_workpackages_by_project_id(args.project_id, status=args.status)
        else:
            return client.get_workpackages(status=args.status)

    elif mode == 'get-work-package':
        return client.get_workpackage(args.id)

    elif mode == 'get-types':
        if args.project_id:
            return client.get_types_by_project_id(args.project_id)
        return client.get_types()

    elif mode == 'get-type':
        return client.get_type(args.id)

    elif mode == 'get-priorities':
        return client.get_priorities()

    elif mode == 'get-priority':
        return client.get_priority(args.id)

    elif mode == 'get-categories':
        return client.get_categories_by_project_id(args.project_id)

    elif mode == 'get-category':
        return client.get_category(args.id)

    elif mode == 'get-relations':
        return client.get_relations()

    elif mode == 'get-relation':
        return client.get_relation(args.id)

    elif mode == 'get-versions':
        return client.get_versions()

    elif mode == 'get-version':
        return client.get_version(args.id)

    elif mode == 'get-users':
        return client.get_users()

    elif mode == 'get-user':
        return client.get_user(args.id)

    elif mode == 'get-placeholder-users':
        return client.get_placeholder_users()

    elif mode == 'get-placeholder-user':
        return client.get_placeholder_user(args.id)

    elif mode == 'get-memberships':
        return client.get_project_members()

    elif mode == 'get-membership':
        return client.get_project_member(args.id)

    elif mode == 'get-statuses':
        return client.get_statuses()

    elif mode == 'get-status':
        return client.get_status(args.id)

    elif mode == 'get-time-entries':
        return client.get_time_entries(
            work_package_id=args.work_package_id,
            project_id=args.project_id,
        )

    elif mode == 'get-time-entry':
        return client.get_time_entry(args.id)

    elif mode == 'get-activities':
        return client.get_activities(args.id)

    elif mode == 'get-attachments':
        return client.get_attachments_by_work_package(args.id)

    elif mode == 'get-attachment':
        return client.get_attachment(args.id)

    elif mode == 'get-notifications':
        return client.get_notifications()

    elif mode == 'get-notification':
        return client.get_notification(args.id)

    elif mode == 'get-grids':
        return client.get_grids(scope=args.scope)

    elif mode == 'get-grid':
        return client.get_grid(args.id)

    elif mode == 'get-query':
        return client.get_query(args.id)

    # write commands
    elif mode == 'create-work-package':
        return client.create_workpackage(
            project_id=args.project_id, subject=args.subject,
            type_id=args.type_id, status_id=args.status_id,
            assignee_id=args.assignee_id, responsible_id=args.responsible_id,
            priority_id=args.priority_id, version_id=args.version_id,
            parent_id=args.parent_id, category_id=args.category_id,
            budget_id=args.budget_id,
            start_date=args.start_date, due_date=args.due_date,
            estimated_time=args.estimated_time,
            percentage_done=args.percentage_done,
            description=args.description,
            schedule_manually=args.schedule_manually,
        )

    elif mode == 'update-work-package':
        wp = client.get_workpackage(args.id)
        return client.update_workpackage(
            workpackage_id=args.id, lock_version=wp.lockversion,
            subject=args.subject,
            type_id=args.type_id, status_id=args.status_id,
            assignee_id=args.assignee_id, responsible_id=args.responsible_id,
            priority_id=args.priority_id, version_id=args.version_id,
            parent_id=args.parent_id, category_id=args.category_id,
            budget_id=args.budget_id,
            start_date=args.start_date, due_date=args.due_date,
            estimated_time=args.estimated_time,
            remaining_time=args.remaining_time,
            percentage_done=args.percentage_done,
            description=args.description,
            schedule_manually=args.schedule_manually,
        )

    elif mode == 'add-comment':
        return client.add_workpackage_comment(args.id, args.message)

    elif mode == 'create-relation':
        return client.create_relation(
            from_id=args.from_id, to_id=args.to_id,
            relation_type=args.relation_type,
            description=args.description, lag=args.lag,
        )

    elif mode == 'create-time-entry':
        return client.create_time_entry(
            work_package_id=args.work_package_id,
            hours=args.hours, spent_on=args.spent_on,
            activity_id=args.activity_id, comment=args.comment,
            project_id=args.project_id,
        )

    elif mode == 'update-time-entry':
        te = client.get_time_entry(args.id)
        return client.update_time_entry(
            entry_id=args.id, lock_version=te.lockversion,
            hours=args.hours, spent_on=args.spent_on,
            activity_id=args.activity_id, comment=args.comment,
        )

    elif mode == 'mark-notification-read':
        return client.mark_notification_read(args.id)

    elif mode == 'mark-notification-unread':
        return client.mark_notification_unread(args.id)

    elif mode == 'mark-all-notifications-read':
        return client.mark_all_notifications_read()

    # delete commands
    elif mode == 'delete-work-package':
        return client.delete_workpackage(args.id)

    elif mode == 'delete-relation':
        return client.delete_relation(args.id)

    elif mode == 'delete-time-entry':
        return client.delete_time_entry(args.id)

    elif mode == 'delete-attachment':
        return client.delete_attachment(args.id)

    else:
        return None


def text_out(data):
    """Print resource(s) in human-readable text format."""
    if isinstance(data, list):
        for item in data:
            print(item)
    else:
        print(data)


def json_out(data):
    """Print resource(s) as formatted JSON."""
    if isinstance(data, list):
        items = [_obj_to_dict(item) for item in data]
        print(json.dumps(items, default=str, sort_keys=True, indent=2))
    else:
        print(json.dumps(_obj_to_dict(data), default=str, sort_keys=True, indent=2))


def _obj_to_dict(obj):
    """Convert an object to a dict, filtering out private attributes."""
    if isinstance(obj, dict):
        return obj
    d = {}
    for k, v in obj.__dict__.items():
        if k.startswith('_'):
            continue
        if isinstance(v, list):
            d[k] = [_obj_to_dict(item) if hasattr(item, '__dict__') else item for item in v]
        elif hasattr(v, '__dict__') and not callable(v):
            d[k] = _obj_to_dict(v)
        else:
            d[k] = v
    return d
