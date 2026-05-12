"""Client for the OpenProject API v3.

Provides a simple interface to read and write data from any OpenProject
instance (version 10 and later). Handles pagination, JSON decoding, and maps
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

    def __init__(self, base_url, apikey, *,
                 timeout: float | None = None,
                 verify_ssl: bool | str = True):

        if not base_url:
            raise ApiError('base_url must not be null')

        if not apikey:
            raise ApiError('apikey must be set')

        self._rootpath = 'api/v3'
        self.base_url = base_url
        self.apikey = apikey
        self.auth = HTTPBasicAuth('apikey', apikey)
        self._timeout = timeout
        self._verify_ssl = verify_ssl

        if not self.base_url.endswith('/'):
            self.base_url += '/'

    def _endpoint(self, resource):
        """Build the full API endpoint URL for a resource path."""
        return f"{self.base_url}{self._rootpath}/{resource}"

    def _headers(self, content_type=None):
        """Return standard request headers."""
        h = {
            'Accept': 'application/json;charset=UTF-8',
            'accept-encoding': 'identity, gzip',
        }
        if content_type:
            h['Content-Type'] = content_type
        return h

    def http_get(self, resource, payload=None):
        """Perform an HTTP GET request against the given endpoint."""
        payload = payload or {}
        endpoint = self._endpoint(resource)
        logger.debug("GET %s params=%s", endpoint, payload or "(none)")
        resp = requests.get(
            endpoint,
            params=payload,
            headers=self._headers(),
            auth=self.auth
        )
        logger.debug("GET %s -> %s", endpoint, resp.status_code)
        return resp

    def http_post(self, resource, body):
        """Perform an HTTP POST request with a JSON body."""
        endpoint = self._endpoint(resource)
        logger.debug("POST %s", endpoint)
        resp = requests.post(
            endpoint,
            json=body,
            headers=self._headers('application/json'),
            auth=self.auth
        )
        logger.debug("POST %s -> %s", endpoint, resp.status_code)
        return resp

    def http_patch(self, resource, body):
        """Perform an HTTP PATCH request with a JSON body."""
        endpoint = self._endpoint(resource)
        logger.debug("PATCH %s", endpoint)
        resp = requests.patch(
            endpoint,
            json=body,
            headers=self._headers('application/json'),
            auth=self.auth
        )
        logger.debug("PATCH %s -> %s", endpoint, resp.status_code)
        return resp

    def http_delete(self, resource):
        """Perform an HTTP DELETE request."""
        endpoint = self._endpoint(resource)
        logger.debug("DELETE %s", endpoint)
        resp = requests.delete(
            endpoint,
            headers=self._headers(),
            auth=self.auth
        )
        logger.debug("DELETE %s -> %s", endpoint, resp.status_code)
        return resp

    def get(self, resource, payload=None):
        """GET a resource and decode the response."""
        response = self.http_get(resource, payload)

        if response:
            return self.decode_response(response)
        else:
            return None

    def post(self, resource, body):
        """POST a resource and decode the response.

        Raises RequestError on HTTP 4xx/5xx.
        """
        response = self.http_post(resource, body)
        if response.status_code >= 400:
            raise RequestError(
                f"POST {resource} failed ({response.status_code}): {response.text}"
            )
        return self.decode_response(response)

    def patch(self, resource, body):
        """PATCH a resource and decode the response.

        Raises RequestError on HTTP 4xx/5xx.
        """
        response = self.http_patch(resource, body)
        if response.status_code >= 400:
            raise RequestError(
                f"PATCH {resource} failed ({response.status_code}): {response.text}"
            )
        return self.decode_response(response)

    def delete(self, resource):
        """DELETE a resource.

        Raises RequestError on HTTP 4xx/5xx.
        Returns True on success (204 No Content or 200).
        """
        response = self.http_delete(resource)
        if response.status_code >= 400:
            raise RequestError(
                f"DELETE {resource} failed ({response.status_code}): {response.text}"
            )
        return True

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

        :param status: one of 'all', 'open', 'closed' (case-insensitive). Unknown values are
            ignored (no filter applied) and a debug log entry is emitted. If both `status` and
            `status_ids` are provided, `status` takes precedence.
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
                logger.debug("Unknown status filter: %s (no filter applied)", status)
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
                logger.debug("Unknown status filter: %s (no filter applied)", status)
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
        payload = {'pageSize': page_size}
        offset = 1

        while True:
            payload.update({'offset': offset})
            result = self.get(f"queries/{query_id}", payload=payload)
            if result:
                collection = result.results
                if isinstance(collection, res.WorkPackageCollection):
                    workpackages += list(result.results)

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

    def get_type(self, type_id: int) -> res.Type:
        """Fetch a single work package type by ID."""
        return self.get(f"types/{type_id}")

    def get_types(self) -> list[res.Type]:
        """Fetch all work package types."""
        return self.get_paged_collection("types", page_size=100)

    def get_types_by_project_id(self, project_id: int) -> list[res.Type]:
        """Fetch work package types available in a project."""
        return self.get_paged_collection(f"projects/{project_id}/types", page_size=100)

    def get_priority(self, priority_id: int) -> res.Priority:
        """Fetch a single priority by ID."""
        return self.get(f"priorities/{priority_id}")

    def get_priorities(self) -> list[res.Priority]:
        """Fetch all priorities."""
        return self.get_paged_collection("priorities", page_size=100)

    def get_category(self, category_id: int) -> res.Category:
        """Fetch a single category by ID."""
        return self.get(f"categories/{category_id}")

    def get_categories_by_project_id(self, project_id: int) -> list[res.Category]:
        """Fetch all categories for a project."""
        return self.get_paged_collection(f"projects/{project_id}/categories", page_size=100)

    def get_time_entry(self, entry_id: int) -> res.TimeEntry:
        """Fetch a single time entry by ID."""
        return self.get(f"time_entries/{entry_id}")

    def get_time_entries(self, work_package_id: int = None, project_id: int = None) -> list[res.TimeEntry]:
        """Fetch time entries, optionally filtered by work package or project."""
        filters = []
        if work_package_id is not None:
            filters.append({"work_package": {"operator": "=", "values": [str(work_package_id)]}})
        if project_id is not None:
            filters.append({"project": {"operator": "=", "values": [str(project_id)]}})

        payload = {}
        if filters:
            payload['filters'] = json.dumps(filters)

        return self.get_paged_collection("time_entries", page_size=100, payload=payload)

    def get_activities(self, work_package_id: int) -> list[res.Activity]:
        """Fetch all activities (journal entries) for a work package."""
        result = self.get(f"work_packages/{work_package_id}/activities")
        if result and hasattr(result, '__iter__'):
            return list(result)
        return []

    def get_attachment(self, attachment_id: int) -> res.Attachment:
        """Fetch a single attachment by ID."""
        return self.get(f"attachments/{attachment_id}")

    def get_attachments_by_work_package(self, work_package_id: int) -> list[res.Attachment]:
        """Fetch all attachments for a work package."""
        result = self.get(f"work_packages/{work_package_id}/attachments")
        if result and hasattr(result, '__iter__'):
            return list(result)
        return []

    def get_notifications(self, *, unread_only: bool = False) -> list[res.Notification]:
        """Fetch all notifications for the current user."""
        payload = {}
        if unread_only:
            payload['filters'] = '[{"readIAN":{"operator":"=","values":["f"]}}]'
        return self.get_paged_collection("notifications", page_size=100, payload=payload)

    def get_notification(self, notification_id: int) -> res.Notification:
        """Fetch a single notification by ID."""
        return self.get(f"notifications/{notification_id}")

    # write methods
    # ###################################################

    def create_workpackage(self, project_id: int, subject: str, *,
                           type_id: int = None, status_id: int = None,
                           assignee_id: int = None, responsible_id: int = None,
                           priority_id: int = None, version_id: int = None,
                           parent_id: int = None, category_id: int = None,
                           budget_id: int = None,
                           start_date: str = None, due_date: str = None,
                           estimated_time: str = None,
                           percentage_done: int = None,
                           description: str = None,
                           schedule_manually: bool = None) -> res.WorkPackage:
        """Create a new work package in a project."""
        body = {"subject": subject}

        if description is not None:
            body["description"] = {"raw": description}
        if start_date is not None:
            body["startDate"] = start_date
        if due_date is not None:
            body["dueDate"] = due_date
        if estimated_time is not None:
            body["estimatedTime"] = estimated_time
        if percentage_done is not None:
            body["percentageDone"] = percentage_done
        if schedule_manually is not None:
            body["scheduleManually"] = schedule_manually

        links = {}
        if type_id is not None:
            links["type"] = {"href": f"/api/v3/types/{type_id}"}
        if status_id is not None:
            links["status"] = {"href": f"/api/v3/statuses/{status_id}"}
        if assignee_id is not None:
            links["assignee"] = {"href": f"/api/v3/users/{assignee_id}"}
        if responsible_id is not None:
            links["responsible"] = {"href": f"/api/v3/users/{responsible_id}"}
        if priority_id is not None:
            links["priority"] = {"href": f"/api/v3/priorities/{priority_id}"}
        if version_id is not None:
            links["version"] = {"href": f"/api/v3/versions/{version_id}"}
        if parent_id is not None:
            links["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}
        if category_id is not None:
            links["category"] = {"href": f"/api/v3/categories/{category_id}"}
        if budget_id is not None:
            links["budget"] = {"href": f"/api/v3/budgets/{budget_id}"}
        if links:
            body["_links"] = links

        return self.post(f"projects/{project_id}/work_packages", body)

    def update_workpackage(self, workpackage_id: int, lock_version: int, *,
                           subject: str = None,
                           type_id: int = None, status_id: int = None,
                           assignee_id: int = None, responsible_id: int = None,
                           priority_id: int = None, version_id: int = None,
                           parent_id: int = None, category_id: int = None,
                           budget_id: int = None,
                           start_date: str = None, due_date: str = None,
                           estimated_time: str = None,
                           percentage_done: int = None,
                           description: str = None,
                           schedule_manually: bool = None,
                           remaining_time: str = None) -> res.WorkPackage:
        """Update an existing work package.

        lock_version is required for optimistic locking.
        """
        body = {"lockVersion": lock_version}

        if subject is not None:
            body["subject"] = subject
        if description is not None:
            body["description"] = {"raw": description}
        if start_date is not None:
            body["startDate"] = start_date
        if due_date is not None:
            body["dueDate"] = due_date
        if estimated_time is not None:
            body["estimatedTime"] = estimated_time
        if percentage_done is not None:
            body["percentageDone"] = percentage_done
        if schedule_manually is not None:
            body["scheduleManually"] = schedule_manually
        if remaining_time is not None:
            body["remainingTime"] = remaining_time

        links = {}
        if type_id is not None:
            links["type"] = {"href": f"/api/v3/types/{type_id}"}
        if status_id is not None:
            links["status"] = {"href": f"/api/v3/statuses/{status_id}"}
        if assignee_id is not None:
            links["assignee"] = {"href": f"/api/v3/users/{assignee_id}"}
        if responsible_id is not None:
            links["responsible"] = {"href": f"/api/v3/users/{responsible_id}"}
        if priority_id is not None:
            links["priority"] = {"href": f"/api/v3/priorities/{priority_id}"}
        if version_id is not None:
            links["version"] = {"href": f"/api/v3/versions/{version_id}"}
        if parent_id is not None:
            links["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}
        if category_id is not None:
            links["category"] = {"href": f"/api/v3/categories/{category_id}"}
        if budget_id is not None:
            links["budget"] = {"href": f"/api/v3/budgets/{budget_id}"}
        if links:
            body["_links"] = links

        return self.patch(f"work_packages/{workpackage_id}", body)

    def add_workpackage_comment(self, workpackage_id: int, message: str) -> res.GenericType:
        """Add a comment (activity) to a work package."""
        body = {
            "comment": {"raw": message},
        }
        return self.post(f"work_packages/{workpackage_id}/activities", body)

    def create_relation(self, from_id: int, to_id: int, relation_type: str,
                        *, description: str = None, lag: int = None) -> res.Relation:
        """Create a relation between two work packages.

        relation_type: one of relates, duplicates, duplicated, blocks, blocked,
                       precedes, follows, includes, partof, requires, required
        """
        body = {
            "type": relation_type,
            "_links": {
                "from": {"href": f"/api/v3/work_packages/{from_id}"},
                "to": {"href": f"/api/v3/work_packages/{to_id}"},
            },
        }
        if description is not None:
            body["description"] = description
        if lag is not None:
            body["lag"] = lag

        return self.post("relations", body)

    # delete methods
    # ###################################################

    def delete_workpackage(self, workpackage_id: int) -> bool:
        """Delete a work package by ID."""
        return self.delete(f"work_packages/{workpackage_id}")

    def delete_relation(self, relation_id: int) -> bool:
        """Delete a relation by ID."""
        return self.delete(f"relations/{relation_id}")

    def delete_attachment(self, attachment_id: int) -> bool:
        """Delete an attachment by ID."""
        return self.delete(f"attachments/{attachment_id}")

    def delete_time_entry(self, entry_id: int) -> bool:
        """Delete a time entry by ID."""
        return self.delete(f"time_entries/{entry_id}")

    # time entry write methods
    # ###################################################

    def create_time_entry(self, work_package_id: int, hours: str, spent_on: str, *,
                          activity_id: int = None, comment: str = None,
                          project_id: int = None) -> res.TimeEntry:
        """Create a time entry on a work package.

        hours: ISO 8601 duration (e.g. PT1H30M)
        spent_on: date (YYYY-MM-DD)
        """
        body = {
            "hours": hours,
            "spentOn": spent_on,
            "_links": {
                "workPackage": {"href": f"/api/v3/work_packages/{work_package_id}"},
            },
        }
        if comment is not None:
            body["comment"] = {"raw": comment}
        if project_id is not None:
            body["_links"]["project"] = {"href": f"/api/v3/projects/{project_id}"}
        if activity_id is not None:
            body["_links"]["activity"] = {"href": f"/api/v3/time_entries/activities/{activity_id}"}

        return self.post("time_entries", body)

    def update_time_entry(self, entry_id: int, lock_version: int, *,
                          hours: str = None, spent_on: str = None,
                          activity_id: int = None, comment: str = None) -> res.TimeEntry:
        """Update an existing time entry."""
        body = {"lockVersion": lock_version}
        if hours is not None:
            body["hours"] = hours
        if spent_on is not None:
            body["spentOn"] = spent_on
        if comment is not None:
            body["comment"] = {"raw": comment}

        links = {}
        if activity_id is not None:
            links["activity"] = {"href": f"/api/v3/time_entries/activities/{activity_id}"}
        if links:
            body["_links"] = links

        return self.patch(f"time_entries/{entry_id}", body)

    # notification write methods
    # ###################################################

    def mark_notification_read(self, notification_id: int) -> res.Notification:
        """Mark a notification as read."""
        return self.patch(f"notifications/{notification_id}", {"readIAN": True})  # API expects camelCase

    def mark_notification_unread(self, notification_id: int) -> res.Notification:
        """Mark a notification as unread."""
        return self.patch(f"notifications/{notification_id}", {"readIAN": False})

    def mark_all_notifications_read(self) -> bool:
        """Mark all notifications as read."""
        response = self.http_post("notifications/read_ian", {})
        if response.status_code >= 400:
            raise RequestError(
                f"POST notifications/read_ian failed ({response.status_code}): {response.text}"
            )
        return True


class ApiError(Exception):
    pass


class RequestError(Exception):
    pass
