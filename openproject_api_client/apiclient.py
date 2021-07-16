import json
import sys
from types import SimpleNamespace
from typing import List

import requests
from requests.auth import HTTPBasicAuth

# import types
import openproject_api_client.resources as res


# https://docs.openproject.org/api/

# https://community.openproject.com/topics/7941

class ApiClient(object):

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

    # decorating function for error handling
    # def safe_request(fct):
    #     """ Return Go-like data (i.e. actual response and possible error) instead of raising errors. """
    #     def inner(*args, **kwargs):
    #         data, error = {}
    #
    #         try:
    #             res = fct(*args, **kwargs)
    #         except requests.exceptions.ConnectionError as error:
    #             return None, {'message': str(error), 'id': -1}
    #
    #         if res.status_code == 200 and res.headers['content-type'] == 'application/json':
    #             # expected behavior
    #             data = res.json()
    #         elif res.status_code == 206 and res.headers['content-type'] == 'application/json':
    #             # partial response, return as-is
    #             data = res.json()
    #         else:
    #             # something went wrong
    #             error = {'id': res.status_code, 'message': res.reason}
    #
    #         return res, error
    #     return inner

    # @safe_request
    def http_get(self, resource, payload=None):
        """ Perform an HTTP GET request against the given endpoint. """
        # Avoid dangerous default function argument `{}`
        payload = payload or {}
        # versioning an API guarantees compatibility
        endpoint = '{}{}/{}'.format(self.base_url, self._rootpath, resource)
        return requests.get(
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

    def get(self, resource, payload=None):
        """
        a get method for a generic endpoint

        :param resource:
        :param payload:
        :return:
        """

        response = self.http_get(resource, payload)

        # if response.status_code == 200 and response.headers['content-type'] == 'application/json':
        if response:
            return self.decode_response(response)
        else:
            return None

    def get_paged_collection(self, resource: str, payload: object = None, page_size: int = 5) -> List[res.GenericType]:
        elements = []

        payload = payload or {}
        payload.update({'pageSize': page_size})

        offset = 1
        while True:
            payload.update({'offset': offset})
            collection = self.get(resource, payload=payload)
            if collection:
                elements += list(collection)
                if collection.total < collection.offset * collection.pagesize:
                    break
                offset += 1
            else:
                break

        return elements

    @staticmethod
    def decode_response(response):
        try:
            # try to decode json object depending on type
            return ApiClient.decode(response.json())

        except:
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
                print(f"*warn* unable to instantiate class for type {json_object['_type']}, error was: {e}")
                # class not found, using generic class
                return res.GenericType(json_object, debug=True)

        raise ApiError

    # methods for specific/convenient access to endpoints
    # ###################################################

    def get_projects(self) -> List[res.Project]:
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
        projects = self.get('projects')
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
        return self.get(f"work_packages/{workpackage_id}")

    def get_workpackages(self):
        raise NotImplemented

    def get_workpackages_by_project_id(self, project_id: int, status: str = None, status_ids: List[int] = None) -> List[res.WorkPackage]:
        """
        fetched workpackages for a specific projects

        :param project_id: project to list workpackages for
        :type project_id: int
        :param status: one of 'all', 'open' (default), 'closed' ; overrides status_ids
        :type status: str
        :param status_ids: list of status ids used to filter ; when using status must not be set
        :type status_ids: int
        :return: returns list of workpackages of requested project and filter
        :rtype: List[WorkPackage]
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

        # filters.append({"subProject": {"operator": "=", "values": "none"}})

        payload = {}
        if len(filters):
            payload.update({'filters': json.dumps(filters)})

        return self.get_paged_collection(f"projects/{project_id}/work_packages", page_size=100, payload=payload)

    def get_workpackages_by_query_id(self, query_id: int) -> List[res.WorkPackage]:
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
        return self.get(f"relations/{relation_id}")

    def get_relations(self) -> List[res.Relation]:
        result = self.get(f"relations")
        if result:
            return (list(result))

        return None

    def get_version(self, version_id: int) -> res.Version:
        return self.get(f"versions/{version_id}")

    def get_versions(self) -> List[res.Version]:
        result = self.get(f"versions")

        if result:
            return (list(result))

        return None

    def get_user(self, user_id: int) -> res.User:
        return self.get(f"users/{user_id}")

    def get_users(self) -> List[res.User]:
        result = self.get(f"users")

        if result:
            return (list(result))

        return None

    def get_placeholder_users(self, user_id: int) -> res.PlaceholderUser:
        return self.get(f"placeholder_users/{user_id}")

    def get_placeholder_users(self) -> List[res.PlaceholderUser]:
        result = self.get(f"placeholder_users")

        if result:
            return (list(result))

        return None

    def get_project_member(self, id: int) -> res.Membership:
        return self.get(f"memberships/{id}")

    def get_project_members(self) -> List[res.Membership]:
        result = self.get(f"memberships")

        if result:
            return (list(result))

        return None

    def get_status(self, id: int) -> res.Status:
        return self.get(f"statuses/{id}")

    def get_statuses(self) -> List[res.Status]:
        result = self.get(f"statuses")

        if result:
            return (list(result))

        return None

    def get_version(self, id: int) -> res.Version:
        return self.get(f"versions/{id}")

    def get_versions(self) -> List[res.Version]:
        result = self.get(f"versions")

        if result:
            return (list(result))

        return None

    def get_grid(self, grid_id: int) -> res.Grid:
        return self.get(f"grids/{grid_id}")

    def get_grids(self, scope: str = None) -> List[res.Grid]:
        # build filter
        filters = []
        if scope:
            filters.append({"scope": {"operator": "=", "values": [scope]}})

        payload = {}
        if len(filters):
            payload.update({'filters': json.dumps(filters)})

        return self.get_paged_collection(f"grids", page_size=100, payload=payload)

    def get_query(self, query_id: int) -> res.Query:
        # we do not need any elements in here, use get_workpackages_by_query_id functions
        return self.get(f"queries/{query_id}", payload={'pageSize': 0})


class ApiError(Exception):
    pass


class RequestError(Exception):
    pass
