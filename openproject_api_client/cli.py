import argparse
import os
import json
import sys

import openproject_api_client as opc


def main():
    parser = argparse.ArgumentParser(description='openproject api client')
    parser.add_argument('--apikey', help='api key to access', metavar='apikey', dest='apikey',
                        required=False)
    parser.add_argument('--baseurl', help='baseurl of openproject', metavar='baseurl', dest='baseurl',
                        required=False)
    parser.add_argument('--json', help='output as json', action='store_true', dest='json')

    subparsers = parser.add_subparsers(dest='mode')

    # projects
    sp_projects = subparsers.add_parser('projects', help='list all projects')

    # work-packages
    sp_wp = subparsers.add_parser('work-packages', help='list work packages')
    sp_wp.add_argument('--project-id', type=int, help='filter by project id')
    sp_wp.add_argument('--query-id', type=int, help='fetch work packages by saved query id')
    sp_wp.add_argument('--status', choices=['all', 'open', 'closed'], default=None,
                       help='filter by status')

    # work-package (single)
    sp_wp_single = subparsers.add_parser('work-package', help='get a single work package')
    sp_wp_single.add_argument('id', type=int, help='work package id')

    # relations
    sp_relations = subparsers.add_parser('relations', help='list all relations')

    # relation (single)
    sp_relation = subparsers.add_parser('relation', help='get a single relation')
    sp_relation.add_argument('id', type=int, help='relation id')

    # versions
    sp_versions = subparsers.add_parser('versions', help='list all versions')

    # version (single)
    sp_version = subparsers.add_parser('version', help='get a single version')
    sp_version.add_argument('id', type=int, help='version id')

    # users
    sp_users = subparsers.add_parser('users', help='list all users')

    # user (single)
    sp_user = subparsers.add_parser('user', help='get a single user')
    sp_user.add_argument('id', type=int, help='user id')

    # placeholder-users
    sp_ph_users = subparsers.add_parser('placeholder-users', help='list all placeholder users')

    # placeholder-user (single)
    sp_ph_user = subparsers.add_parser('placeholder-user', help='get a single placeholder user')
    sp_ph_user.add_argument('id', type=int, help='placeholder user id')

    # memberships
    sp_members = subparsers.add_parser('memberships', help='list all memberships')

    # membership (single)
    sp_member = subparsers.add_parser('membership', help='get a single membership')
    sp_member.add_argument('id', type=int, help='membership id')

    # statuses
    sp_statuses = subparsers.add_parser('statuses', help='list all statuses')

    # status (single)
    sp_status = subparsers.add_parser('status', help='get a single status')
    sp_status.add_argument('id', type=int, help='status id')

    # grids
    sp_grids = subparsers.add_parser('grids', help='list all grids')
    sp_grids.add_argument('--scope', help='filter by scope')

    # grid (single)
    sp_grid = subparsers.add_parser('grid', help='get a single grid')
    sp_grid.add_argument('id', type=int, help='grid id')

    # queries (single only, since list is not paginated the same way)
    sp_query = subparsers.add_parser('query', help='get a single query')
    sp_query.add_argument('id', type=int, help='query id')

    args = parser.parse_args()

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
        if result is not None:
            if args.json:
                json_out(result)
            else:
                text_out(result)

    except opc.ApiError as err:
        print(f"error during request: {err}", file=sys.stderr)
        sys.exit(1)


def dispatch(client, args):
    """Route the parsed CLI args to the right client method."""
    mode = args.mode

    if mode == 'projects':
        return client.get_projects()

    elif mode == 'work-packages':
        if args.query_id:
            return client.get_workpackages_by_query_id(args.query_id)
        elif args.project_id:
            return client.get_workpackages_by_project_id(args.project_id, status=args.status)
        else:
            return client.get_workpackages(status=args.status)

    elif mode == 'work-package':
        return client.get_workpackage(args.id)

    elif mode == 'relations':
        return client.get_relations()

    elif mode == 'relation':
        return client.get_relation(args.id)

    elif mode == 'versions':
        return client.get_versions()

    elif mode == 'version':
        return client.get_version(args.id)

    elif mode == 'users':
        return client.get_users()

    elif mode == 'user':
        return client.get_user(args.id)

    elif mode == 'placeholder-users':
        return client.get_placeholder_users()

    elif mode == 'placeholder-user':
        return client.get_placeholder_user(args.id)

    elif mode == 'memberships':
        return client.get_project_members()

    elif mode == 'membership':
        return client.get_project_member(args.id)

    elif mode == 'statuses':
        return client.get_statuses()

    elif mode == 'status':
        return client.get_status(args.id)

    elif mode == 'grids':
        return client.get_grids(scope=args.scope)

    elif mode == 'grid':
        return client.get_grid(args.id)

    elif mode == 'query':
        return client.get_query(args.id)

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
