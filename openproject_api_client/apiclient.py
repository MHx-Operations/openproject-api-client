"""Client for the OpenProject API v3.

Provides a simple interface to read data from any OpenProject instance
(version 10 and later). Handles pagination, JSON decoding, and maps
API responses to typed Python objects.
"""

from __future__ import annotations

import json
import logging
import sys
from types import SimpleNamespace

import requests
from requests.auth import HTTPBasicAuth

import openproject_api_client.resources as res

__all__ = ["ApiClient", "ApiError", "RequestError"]

logger = logging.getLogger(__name__)


class ApiClient:
    """Client for the OpenProject API v3.

    Usage::

        client = ApiClient("https://openproject.example.com/", "your-api-key")
        projects = client.get_projects()
        work_packages = client.get_workpackages(status='open')
    """

    def __init__(self, base_url, apikey):

        if not base_url:
            raise ApiError('base_url must not be null')

        if not apikey:
            raise ApiError('apikey must be set')

        self._rootpath = 'api/v3'
        self.base_url = base_url
        self.apikey = apikey
        self.auth = HTTPBasicAuth('apikey', apikey)

        if not self.base_url.endswith('/'):
            self.base_url += '/'

    def http_get(self, resource, payload=None):
        """ Perform an HTTP GET request against the given endpoint. """
        # Avoid dangerous default function argument `{}`
        payload = payload or {}
        # versioning an API guarantees compatibility
        endpoint = f"{self.base_url}{self._rootpath}/{resource}"
        logger.debug("GET %s params=%s", endpoint, payload or "(none)")
        resp = requests.get(
            endpoint,
            # attach parameters to the url, like `&foo=bar`
            params=payload,
            # tell the API we expect to parse JSON responses
            headers={
                'Accept': 'application/json;charset=UTF-8',
                'accept-encoding': 'identity, gzip',
            },
            auth=self.auth
        )
        logger.debug("GET %s -> %s", endpoint, resp.status_code)
        return resp

    def get(self, resource, payload=None):
        """
        a get method for a generic endpoint

        :param resource:
        :param payload:
        :return:
        """

        response = self.http_get(resource, payload)

        if response:
            return self.decode_response(response)
        else:
            return None

    def get_paged_collection(self, resource: str, payload: object = None, page_size: int = 5) -> list[res.GenericType]:
        elements = []

        payload = payload or {}
        payload.update({'pageSize': page_size})

        offset = 1
        while True:
            payload.update({'offset': offset})
            collection = self.get(resource, payload=payload)
            if collection:
                page_items = list(collection)
                elements += page_items
                logger.debug("Paged %s: offset=%d fetched=%d total=%s",
                             resource, offset, len(page_items), collection.total)

                # some collections do not deliver pagesize and offset
                effective_pagesize = page_size
                if collection.pagesize is not None:
                    effective_pagesize = collection.pagesize

                effective_offset = offset
                if collection.offset is not None:
                    effective_offset = collection.offset

                if collection.total < effective_offset * effective_pagesize:
                    break
                offset += 1
            else:
                break

        logger.debug("Paged %s: done, %d elements total", resource, len(elements))
        return elements

    @staticmethod
    def decode_response(response):
        try:
            # try to decode json object depending on type
            return ApiClient.decode(response.json())

        except (ValueError, KeyError):
            # return as SimpleNamespace object if no type info found
            return json.loads(response.text, object_hook=lambda d: SimpleNamespace(**d))

    @staticmethod
    def decode(json_object) -> res.GenericType:

        # if we have a type info, use a specialized class for it
        if '_type' in json_object:
            try:
                clazz = getattr(sys.modules['openproject_api_client.resources'], json_object['_type'])
                obj = clazz(json_object)
                return obj

            except AttributeError as e:
                logger.warning("Unable to instantiate class for type %s: %s", json_object['_type'], e)
                # class not found, using generic class
                return res.GenericType(json_object, debug=True)

        raise ApiError(f"No '_type' key in API response, keys: {list(json_object.keys())}")

    # methods for specific/convenient access to endpoints
    # ###################################################

    def get_projects(self) -> list[res.Project]:
        """
        get an array of all projects

        :return: returns list of all projects
        """
        return list(self.get_projects_dict().values())

    def get_projects_dict(self):
        """
        get all projects as dict

        :return: dict of all project with id as key
        """
        projects = self.get_paged_collection('projects', page_size=100)
        project_map = {}
        for p in projects:
            project_map[p.id] = p

        for i in project_map:
            p = project_map[i]

            while p.parent_id:
                project_map[i].path_ids.insert(0, p.parent_id)
                project_map[i].path.insert(0, project_map[p.parent_id].name)

                p = project_map[p.parent_id]

            project_map[i].level = len(project_map[i].path_ids) + 1
            project_map[i].fullname = '/'.join(project_map[i].path + [project_map[i].name])

        return project_map

    def get_workpackage(self, workpackage_id: int) -> res.WorkPackage:
        """Fetch a single work package by ID."""
        return self.get(f"work_packages/{workpackage_id}")

    def get_workpackages(self, status: str = None, status_ids: list[int] = None, page_size=100) -> list[res.WorkPackage]:
        """
        get all workpackages across all projects

        :param status: one of 'all', 'open' (default), 'closed' ; overrides status_ids
        :type status: str
        :param status_ids: list of status ids used to filter ; when using status must not be set
        :type status_ids: int
        :param page_size: number of items per page
        :type page_size: int
        :return: returns list of all workpackages matching the filter
        :rtype: list[WorkPackage]
        """
        filters = []
        if status is not None:
            if status.lower() == 'all':
                filters.append({"status_id": {"operator": "*", "values": None}})
            elif status.lower() == 'closed':
                filters.append({"status_id": {"operator": "c", "values": None}})
            elif status.lower() == 'open':
                filters.append({"status_id": {"operator": "o", "values": None}})
        else:
            if status_ids is not None:
                filters.append({"status_id": {"operator": "=", "values": status_ids}})

        payload = {}
        if len(filters):
            payload.update({'filters': json.dumps(filters)})

        return self.get_paged_collection('work_packages', page_size=page_size, payload=payload)

    def get_workpackages_by_project_id(self, project_id: int, status: str = None, status_ids: list[int] = None, page_size=100) -> list[res.WorkPackage]:
        """
        fetched workpackages for a specific projects

        :param project_id: project to list workpackages for
        :type project_id: int
        :param status: one of 'all', 'open' (default), 'closed' ; overrides status_ids
        :type status: str
        :param status_ids: list of status ids used to filter ; when using status must not be set
        :type status_ids: int
        :return: returns list of workpackages of requested project and filter
        :rtype: list[WorkPackage]
        """
        # build filter
        filters = []
        if status is not None:
            if status.lower() == 'all':
                filters.append({"status_id": {"operator": "*", "values": None}})
            elif status.lower() == 'closed':
                filters.append({"status_id": {"operator": "c", "values": None}})
            elif status.lower() == 'open':
                filters.append({"status_id": {"operator": "o", "values": None}})
        else:
            if status_ids is not None:
                filters.append({"status_id": {"operator": "=", "values": status_ids}})

        payload = {}
        if len(filters):
            payload.update({'filters': json.dumps(filters)})

        return self.get_paged_collection(f"projects/{project_id}/work_packages", page_size=page_size, payload=payload)

    def get_workpackages_by_query_id(self, query_id: int) -> list[res.WorkPackage]:
        """Fetch all work packages returned by a saved query."""
        workpackages = []
        page_size = 10
        payload={'pageSize': page_size}
        offset = 1

        while True:
            payload.update({'offset': offset})
            result = self.get(f"queries/{query_id}", payload=payload)
            if result:
                collection = result.results
                if isinstance(collection, res.WorkPackageCollection):
                    workpackages += list(result.results)
                    if collection.total < collection.offset * collection.pagesize:
                        break
                    offset += 1
                else:
                    break
            else:
                break
        return workpackages

    def get_relation(self, relation_id: int) -> res.Relation:
        """Fetch a single relation by ID."""
        return self.get(f"relations/{relation_id}")

    def get_relations(self) -> list[res.Relation]:
        """Fetch all work package relations."""
        result = self.get_paged_collection("relations", page_size=500)
        if result:
            return list(result)

        return []

    def get_version(self, version_id: int) -> res.Version:
        """Fetch a single version (milestone) by ID."""
        return self.get(f"versions/{version_id}")

    def get_versions(self) -> list[res.Version]:
        """Fetch all versions across all projects."""
        result = self.get_paged_collection("versions", page_size=100)

        if result:
            return list(result)

        return []

    def get_user(self, user_id: int) -> res.User:
        """Fetch a single user by ID."""
        return self.get(f"users/{user_id}")

    def get_users(self) -> list[res.User]:
        """Fetch all users."""
        result = self.get_paged_collection("users", page_size=100)

        if result:
            return list(result)

        return []

    def get_placeholder_user(self, user_id: int) -> res.PlaceholderUser:
        """Fetch a single placeholder user by ID."""
        return self.get(f"placeholder_users/{user_id}")

    def get_placeholder_users(self) -> list[res.PlaceholderUser]:
        """Fetch all placeholder users."""
        result = self.get_paged_collection("placeholder_users", page_size=100)

        if result:
            return list(result)

        return []

    def get_project_member(self, member_id: int) -> res.Membership:
        """Fetch a single project membership by ID."""
        return self.get(f"memberships/{member_id}")

    def get_project_members(self) -> list[res.Membership]:
        """Fetch all project memberships."""
        result = self.get_paged_collection("memberships", page_size=100)

        if result:
            return list(result)

        return []

    def get_status(self, status_id: int) -> res.Status:
        """Fetch a single work package status by ID."""
        return self.get(f"statuses/{status_id}")

    def get_statuses(self) -> list[res.Status]:
        """Fetch all work package statuses."""
        result = self.get_paged_collection("statuses", page_size=100)

        if result:
            return list(result)

        return []

    def get_grid(self, grid_id: int) -> res.Grid:
        """Fetch a single grid (board) by ID."""
        return self.get(f"grids/{grid_id}")

    def get_grids(self, scope: str = None) -> list[res.Grid]:
        # build filter
        filters = []
        if scope:
            filters.append({"scope": {"operator": "=", "values": [scope]}})

        payload = {}
        if len(filters):
            payload.update({'filters': json.dumps(filters)})

        return self.get_paged_collection("grids", page_size=100, payload=payload)

    def get_query(self, query_id: int) -> res.Query:
        """Fetch a saved query definition (without result elements)."""
        return self.get(f"queries/{query_id}", payload={'pageSize': 0})


class ApiError(Exception):
    pass


class RequestError(Exception):
    pass
