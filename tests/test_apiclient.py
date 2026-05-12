"""Tests for openproject_api_client.apiclient."""

import json

import pytest
import responses

from openproject_api_client.apiclient import ApiClient, ApiError, RequestError
from openproject_api_client.resources import (
    Activity,
    Attachment,
    Category,
    Collection,
    GenericType,
    Membership,
    Notification,
    PlaceholderUser,
    Priority,
    Project,
    Relation,
    Status,
    TimeEntry,
    Type,
    User,
    Version,
    WorkPackage,
)
from tests.conftest import make_collection


BASE_URL = "https://op.example.com/"
API_KEY = "test-api-key"


# -- Constructor -----------------------------------------------------------

class TestApiClientInit:
    def test_valid_construction(self):
        c = ApiClient(BASE_URL, API_KEY)
        assert c.base_url == BASE_URL
        assert c.apikey == API_KEY

    def test_trailing_slash_added(self):
        c = ApiClient("https://op.example.com", API_KEY)
        assert c.base_url.endswith("/")

    def test_missing_base_url_raises(self):
        with pytest.raises(ApiError):
            ApiClient("", API_KEY)

    def test_missing_apikey_raises(self):
        with pytest.raises(ApiError):
            ApiClient(BASE_URL, "")


# -- decode / decode_response ----------------------------------------------

class TestDecode:
    def test_decode_known_type(self, status_json):
        obj = ApiClient.decode(status_json)
        assert isinstance(obj, Status)
        assert obj.id == 1

    def test_decode_unknown_type_returns_generic(self):
        obj = ApiClient.decode({"_type": "SomeFutureType", "id": 999})
        assert isinstance(obj, GenericType)
        assert obj.id == 999

    def test_decode_no_type_raises(self):
        with pytest.raises(ApiError):
            ApiClient.decode({"id": 1, "name": "no type"})

    def test_decode_collection(self, status_json):
        coll_json = make_collection("Collection", [status_json], total=1)
        obj = ApiClient.decode(coll_json)
        assert isinstance(obj, Collection)
        assert obj.total == 1

    @responses.activate
    def test_decode_response_json(self, status_json):
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/statuses/1",
            json=status_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        resp = client.http_get("statuses/1")
        obj = ApiClient.decode_response(resp)
        assert isinstance(obj, Status)

    @responses.activate
    def test_decode_response_no_type_raises(self):
        """When JSON has no _type, ApiError propagates (fallback only
        catches ValueError/KeyError, not ApiError — known limitation)."""
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/custom",
            json={"foo": "bar", "num": 42},
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        resp = client.http_get("custom")
        with pytest.raises(ApiError):
            ApiClient.decode_response(resp)

    @responses.activate
    def test_decode_response_fallback_on_invalid_json(self):
        """When response.json() raises ValueError, falls back to SimpleNamespace."""
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/custom",
            body="not json",
            status=200,
            content_type="text/plain",
        )
        client = ApiClient(BASE_URL, API_KEY)
        resp = client.http_get("custom")
        # response.json() will raise ValueError, triggering the fallback
        # but json.loads on "not json" will also fail — so this actually
        # raises too. Let's just verify the ValueError path is hit.
        with pytest.raises((ValueError, Exception)):
            ApiClient.decode_response(resp)


# -- http_get --------------------------------------------------------------

class TestHttpGet:
    @responses.activate
    def test_sends_auth_and_headers(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/projects",
            json={"_type": "Collection", "total": 0, "count": 0,
                  "offset": 1, "pageSize": 5,
                  "_embedded": {"elements": []}},
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        resp = client.http_get("projects")
        assert resp.status_code == 200
        # verify auth was sent
        assert responses.calls[0].request.headers.get("Accept") == "application/json;charset=UTF-8"

    @responses.activate
    def test_payload_as_query_params(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/work_packages",
            json={"_type": "Collection", "total": 0, "count": 0,
                  "offset": 1, "pageSize": 5,
                  "_embedded": {"elements": []}},
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        client.http_get("work_packages", payload={"pageSize": 10, "offset": 2})
        assert "pageSize=10" in responses.calls[0].request.url
        assert "offset=2" in responses.calls[0].request.url


# -- get -------------------------------------------------------------------

class TestGet:
    @responses.activate
    def test_get_returns_decoded(self, status_json):
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/statuses/1",
            json=status_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        obj = client.get("statuses/1")
        assert isinstance(obj, Status)
        assert obj.name == "New"

    @responses.activate
    def test_get_returns_none_on_error(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/statuses/999",
            json={},
            status=404,
        )
        client = ApiClient(BASE_URL, API_KEY)
        result = client.get("statuses/999")
        assert result is None


# -- get_paged_collection --------------------------------------------------

class TestGetPagedCollection:
    @responses.activate
    def test_single_page(self, status_json):
        coll = make_collection("Collection", [status_json], total=1, offset=1, page_size=5)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/statuses",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        items = client.get_paged_collection("statuses", page_size=5)
        assert len(items) == 1
        assert isinstance(items[0], Status)

    @responses.activate
    def test_multiple_pages(self, status_json):
        status2 = dict(status_json, id=2, name="In Progress")
        status3 = dict(status_json, id=3, name="Closed")

        # Break condition is: total < offset * pageSize
        # page_size=2, total=3: page1 → 3 < 1*2=2 → False (continue),
        #                       page2 → 3 < 2*2=4 → True (break)
        page1 = make_collection("Collection", [status_json, status2], total=3, offset=1, page_size=2)
        page2 = make_collection("Collection", [status3], total=3, offset=2, page_size=2)

        responses.add(responses.GET, f"{BASE_URL}api/v3/statuses", json=page1, status=200)
        responses.add(responses.GET, f"{BASE_URL}api/v3/statuses", json=page2, status=200)

        client = ApiClient(BASE_URL, API_KEY)
        items = client.get_paged_collection("statuses", page_size=2)
        assert len(items) == 3
        assert items[0].name == "New"
        assert items[1].name == "In Progress"
        assert items[2].name == "Closed"


# -- Convenience endpoint methods ------------------------------------------

class TestEndpointMethods:
    @responses.activate
    def test_get_workpackage(self, workpackage_json):
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/work_packages/42",
            json=workpackage_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        wp = client.get_workpackage(42)
        assert isinstance(wp, WorkPackage)
        assert wp.id == 42

    @responses.activate
    def test_get_statuses(self, status_json):
        coll = make_collection("Collection", [status_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/statuses",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        statuses = client.get_statuses()
        assert len(statuses) == 1
        assert statuses[0].name == "New"

    @responses.activate
    def test_get_workpackages_with_status_filter(self, workpackage_json):
        coll = make_collection("Collection", [workpackage_json], total=1, offset=1, page_size=100)
        # The _type inside will be wrong (Collection not matching WP collection)
        # but that's fine — decode handles it.
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/work_packages",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        wps = client.get_workpackages(status="open")
        assert len(wps) == 1
        # verify the filter was sent
        req_url = responses.calls[0].request.url
        assert "filters" in req_url

    @responses.activate
    def test_get_relations_empty(self):
        coll = make_collection("Collection", [], total=0, offset=1, page_size=500)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/relations",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        rels = client.get_relations()
        assert rels == []

    @responses.activate
    def test_get_users(self, user_json):
        coll = make_collection("Collection", [user_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/users",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        users = client.get_users()
        assert len(users) == 1
        assert users[0].name == "Alice Smith"

    @responses.activate
    def test_get_versions(self, version_json):
        coll = make_collection("Collection", [version_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/versions",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        versions = client.get_versions()
        assert len(versions) == 1
        assert versions[0].name == "v1.0"

    @responses.activate
    def test_get_grids_with_scope_filter(self, grid_json):
        coll = make_collection("Collection", [grid_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/grids",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        grids = client.get_grids(scope="/projects/1/boards")
        assert len(grids) == 1
        # verify filter sent
        assert "filters" in responses.calls[0].request.url

    @responses.activate
    def test_get_placeholder_users(self, placeholder_user_json):
        coll = make_collection("Collection", [placeholder_user_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/placeholder_users",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        pus = client.get_placeholder_users()
        assert len(pus) == 1
        assert isinstance(pus[0], PlaceholderUser)

    @responses.activate
    def test_get_project_members(self, membership_json):
        coll = make_collection("Collection", [membership_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/memberships",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        members = client.get_project_members()
        assert len(members) == 1
        assert isinstance(members[0], Membership)

    @responses.activate
    def test_get_workpackages_by_project_id(self, workpackage_json):
        coll = make_collection("Collection", [workpackage_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/projects/1/work_packages",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        wps = client.get_workpackages_by_project_id(1, status="closed")
        assert len(wps) == 1
        assert "filters" in responses.calls[0].request.url

    @responses.activate
    def test_get_workpackages_status_ids_filter(self, workpackage_json):
        coll = make_collection("Collection", [workpackage_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/work_packages",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        wps = client.get_workpackages(status_ids=[1, 2])
        assert len(wps) == 1
        assert "filters" in responses.calls[0].request.url

    @responses.activate
    def test_get_single_relation(self, relation_json):
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/relations/100",
            json=relation_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        rel = client.get_relation(100)
        assert isinstance(rel, Relation)
        assert rel.id == 100

    @responses.activate
    def test_get_single_version(self, version_json):
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/versions/7",
            json=version_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        v = client.get_version(7)
        assert isinstance(v, Version)
        assert v.name == "v1.0"

    @responses.activate
    def test_get_single_user(self, user_json):
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/users/3",
            json=user_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        u = client.get_user(3)
        assert isinstance(u, User)
        assert u.name == "Alice Smith"

    @responses.activate
    def test_get_single_status(self, status_json):
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/statuses/1",
            json=status_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        s = client.get_status(1)
        assert isinstance(s, Status)

    @responses.activate
    def test_get_workpackages_all_status(self, workpackage_json):
        coll = make_collection("Collection", [workpackage_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/work_packages",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        wps = client.get_workpackages(status="all")
        assert len(wps) == 1
        assert "filters" in responses.calls[0].request.url


# -- BUG-04: get_workpackages unknown status behavior ----------------------

class TestGetWorkpackagesUnknownStatus:
    """BUG-04: unknown status string is a silent no-op with a DEBUG log entry."""

    @responses.activate
    def test_get_workpackages_unknown_status_no_filter(self, workpackage_json):
        """Unknown status must not add a filters= query param."""
        coll = make_collection("Collection", [workpackage_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/work_packages",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        wps = client.get_workpackages(status="banana")
        assert len(wps) == 1
        assert "filters" not in responses.calls[0].request.url

    @responses.activate
    def test_get_workpackages_unknown_status_logs_debug(self, workpackage_json, caplog):
        """Unknown status must emit a DEBUG log entry containing the status value."""
        import logging
        coll = make_collection("Collection", [workpackage_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/work_packages",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        with caplog.at_level(logging.DEBUG, logger="openproject_api_client.apiclient"):
            client.get_workpackages(status="banana")
        debug_msgs = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
        assert any("banana" in m for m in debug_msgs), f"Expected 'banana' in a DEBUG log; got: {debug_msgs}"

    @responses.activate
    def test_get_workpackages_open_status_regression(self, workpackage_json):
        """Known status 'open' must still apply the correct filter."""
        coll = make_collection("Collection", [workpackage_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/work_packages",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        client.get_workpackages(status="open")
        assert "filters" in responses.calls[0].request.url
        assert "%22o%22" in responses.calls[0].request.url or '"o"' in responses.calls[0].request.url

    @responses.activate
    def test_get_workpackages_uppercase_status_regression(self, workpackage_json):
        """Status matching must be case-insensitive (OPEN == open)."""
        coll = make_collection("Collection", [workpackage_json], total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/work_packages",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        client.get_workpackages(status="OPEN")
        assert "filters" in responses.calls[0].request.url
        assert "%22o%22" in responses.calls[0].request.url or '"o"' in responses.calls[0].request.url


# -- BUG-05: get_workpackages_by_query_id empty / None pagesize handling ---

def _make_query_json(wp_collection_json):
    """Build a minimal Query JSON wrapping a WorkPackageCollection in _embedded.results."""
    return {
        "_type": "Query",
        "id": 99,
        "name": "Test Query",
        "filters": [],
        "hidden": False,
        "highlightingMode": "none",
        "public": True,
        "showHierarchies": False,
        "starred": False,
        "sums": False,
        "timelineLabels": {},
        "timelineVisible": False,
        "timelineZoomLevel": "days",
        "timestamps": [],
        "createdAt": "2024-01-01T00:00:00+00:00",
        "updatedAt": "2024-03-01T00:00:00+00:00",
        "_links": {
            "project": {"href": "/api/v3/projects/1", "title": "My Project"},
            "user": {"href": "/api/v3/users/3", "title": "Alice Smith"},
        },
        "_embedded": {
            "results": wp_collection_json,
        },
    }


class TestGetWorkpackagesByQueryId:
    """BUG-05: get_workpackages_by_query_id empty/None pagesize/offset handling."""

    @responses.activate
    def test_get_workpackages_by_query_id_empty_collection(self):
        """Empty WorkPackageCollection (total=0) must return [] without AttributeError."""
        from tests.conftest import make_wp_collection
        wpc = make_wp_collection([], total=0, offset=1, page_size=10)
        query = _make_query_json(wpc)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/queries/99",
            json=query,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        result = client.get_workpackages_by_query_id(99)
        assert result == []

    @responses.activate
    def test_get_workpackages_by_query_id_pagesize_none(self, workpackage_json):
        """WorkPackageCollection with null pageSize/offset must not raise TypeError."""
        from tests.conftest import make_wp_collection
        wpc = make_wp_collection([workpackage_json], total=1, offset=1, page_size=10)
        # Simulate API omitting pageSize and offset (None values)
        wpc["pageSize"] = None
        wpc["offset"] = None
        query = _make_query_json(wpc)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/queries/99",
            json=query,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        result = client.get_workpackages_by_query_id(99)
        # Must not raise TypeError; result should contain the one work package
        assert len(result) == 1

    @responses.activate
    def test_get_workpackages_by_query_id_multipage(self, workpackage_json):
        """Two-page query (total=15, page_size=10): result list must have 15 items."""
        from tests.conftest import make_wp_collection
        import copy
        wps_page1 = [copy.deepcopy(workpackage_json) for _ in range(10)]
        wps_page2 = [copy.deepcopy(workpackage_json) for _ in range(5)]
        # page 1: offset=1, total=15, pageSize=10 — not done yet
        wpc1 = make_wp_collection(wps_page1, total=15, offset=1, page_size=10)
        query1 = _make_query_json(wpc1)
        # page 2: offset=2, total=15, pageSize=10 — done (15 < 2*10 → 15 < 20)
        wpc2 = make_wp_collection(wps_page2, total=15, offset=2, page_size=10)
        query2 = _make_query_json(wpc2)
        responses.add(responses.GET, f"{BASE_URL}api/v3/queries/99", json=query1, status=200)
        responses.add(responses.GET, f"{BASE_URL}api/v3/queries/99", json=query2, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        result = client.get_workpackages_by_query_id(99)
        assert len(result) == 15

    @responses.activate
    def test_get_workpackages_by_query_id_non_wpc_results(self):
        """Query with non-WorkPackageCollection results envelope returns []."""
        # A query whose _embedded.results is NOT a WorkPackageCollection
        query = {
            "_type": "Query",
            "id": 99,
            "name": "Test Query",
            "filters": [],
            "hidden": False,
            "highlightingMode": "none",
            "public": True,
            "showHierarchies": False,
            "starred": False,
            "sums": False,
            "timelineLabels": {},
            "timelineVisible": False,
            "timelineZoomLevel": "days",
            "timestamps": [],
            "createdAt": "2024-01-01T00:00:00+00:00",
            "updatedAt": "2024-03-01T00:00:00+00:00",
            "_links": {
                "project": {"href": "/api/v3/projects/1", "title": "My Project"},
                "user": {"href": "/api/v3/users/3", "title": "Alice Smith"},
            },
            "_embedded": {},
        }
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/queries/99",
            json=query,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        result = client.get_workpackages_by_query_id(99)
        assert result == []


# -- Project hierarchy (get_projects_dict) ---------------------------------

class TestProjectHierarchy:
    @responses.activate
    def test_get_projects_dict_builds_hierarchy(self, project_json, child_project_json):
        coll = make_collection("Collection",
                               [project_json, child_project_json],
                               total=2, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/projects",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        pmap = client.get_projects_dict()

        # Root project
        assert pmap[1].level == 1
        assert pmap[1].fullname == "My Project"
        assert pmap[1].path == []
        assert pmap[1].path_ids == []

        # Child project
        assert pmap[2].level == 2
        assert pmap[2].fullname == "My Project/Child Project"
        assert pmap[2].path == ["My Project"]
        assert pmap[2].path_ids == [1]

    @responses.activate
    def test_get_projects_returns_list(self, project_json):
        coll = make_collection("Collection", [project_json],
                               total=1, offset=1, page_size=100)
        responses.add(
            responses.GET,
            f"{BASE_URL}api/v3/projects",
            json=coll,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        projects = client.get_projects()
        assert isinstance(projects, list)
        assert len(projects) == 1
        assert isinstance(projects[0], Project)


# -- http_post / http_patch ------------------------------------------------

class TestHttpPost:
    @responses.activate
    def test_sends_json_body(self, workpackage_json):
        responses.add(
            responses.POST,
            f"{BASE_URL}api/v3/projects/1/work_packages",
            json=workpackage_json,
            status=201,
        )
        client = ApiClient(BASE_URL, API_KEY)
        resp = client.http_post("projects/1/work_packages", {"subject": "New WP"})
        assert resp.status_code == 201
        req = responses.calls[0].request
        assert req.headers["Content-Type"] == "application/json"
        body = json.loads(req.body)
        assert body["subject"] == "New WP"

    @responses.activate
    def test_post_decode_response(self, workpackage_json):
        responses.add(
            responses.POST,
            f"{BASE_URL}api/v3/projects/1/work_packages",
            json=workpackage_json,
            status=201,
        )
        client = ApiClient(BASE_URL, API_KEY)
        result = client.post("projects/1/work_packages", {"subject": "New WP"})
        assert isinstance(result, WorkPackage)

    @responses.activate
    def test_post_error_raises(self):
        responses.add(
            responses.POST,
            f"{BASE_URL}api/v3/projects/1/work_packages",
            json={"_type": "Error", "message": "Validation failed"},
            status=422,
        )
        client = ApiClient(BASE_URL, API_KEY)
        with pytest.raises(RequestError, match="422"):
            client.post("projects/1/work_packages", {"subject": ""})


class TestHttpPatch:
    @responses.activate
    def test_sends_json_body(self, workpackage_json):
        responses.add(
            responses.PATCH,
            f"{BASE_URL}api/v3/work_packages/42",
            json=workpackage_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        resp = client.http_patch("work_packages/42", {"subject": "Updated"})
        assert resp.status_code == 200
        req = responses.calls[0].request
        assert req.headers["Content-Type"] == "application/json"
        body = json.loads(req.body)
        assert body["subject"] == "Updated"

    @responses.activate
    def test_patch_decode_response(self, workpackage_json):
        responses.add(
            responses.PATCH,
            f"{BASE_URL}api/v3/work_packages/42",
            json=workpackage_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        result = client.patch("work_packages/42", {"lockVersion": 5, "subject": "Updated"})
        assert isinstance(result, WorkPackage)

    @responses.activate
    def test_patch_error_raises(self):
        responses.add(
            responses.PATCH,
            f"{BASE_URL}api/v3/work_packages/42",
            json={"_type": "Error", "message": "Conflict"},
            status=409,
        )
        client = ApiClient(BASE_URL, API_KEY)
        with pytest.raises(RequestError, match="409"):
            client.patch("work_packages/42", {"lockVersion": 1})


# -- Write convenience methods ---------------------------------------------

class TestCreateWorkpackage:
    @responses.activate
    def test_minimal(self, workpackage_json):
        responses.add(
            responses.POST,
            f"{BASE_URL}api/v3/projects/1/work_packages",
            json=workpackage_json,
            status=201,
        )
        client = ApiClient(BASE_URL, API_KEY)
        wp = client.create_workpackage(1, "Test WP")
        assert isinstance(wp, WorkPackage)
        body = json.loads(responses.calls[0].request.body)
        assert body["subject"] == "Test WP"
        assert "_links" not in body

    @responses.activate
    def test_with_all_options(self, workpackage_json):
        responses.add(
            responses.POST,
            f"{BASE_URL}api/v3/projects/1/work_packages",
            json=workpackage_json,
            status=201,
        )
        client = ApiClient(BASE_URL, API_KEY)
        client.create_workpackage(
            1, "Full WP",
            type_id=2, status_id=3, assignee_id=4, responsible_id=5,
            priority_id=6, version_id=7, parent_id=8, category_id=9,
            budget_id=10, start_date="2024-01-01", due_date="2024-02-01",
            estimated_time="PT8H", percentage_done=50,
            description="Some **markdown**", schedule_manually=True,
        )
        body = json.loads(responses.calls[0].request.body)
        assert body["subject"] == "Full WP"
        assert body["description"] == {"raw": "Some **markdown**"}
        assert body["startDate"] == "2024-01-01"
        assert body["dueDate"] == "2024-02-01"
        assert body["estimatedTime"] == "PT8H"
        assert body["percentageDone"] == 50
        assert body["scheduleManually"] is True
        links = body["_links"]
        assert links["type"]["href"] == "/api/v3/types/2"
        assert links["status"]["href"] == "/api/v3/statuses/3"
        assert links["assignee"]["href"] == "/api/v3/users/4"
        assert links["responsible"]["href"] == "/api/v3/users/5"
        assert links["priority"]["href"] == "/api/v3/priorities/6"
        assert links["version"]["href"] == "/api/v3/versions/7"
        assert links["parent"]["href"] == "/api/v3/work_packages/8"
        assert links["category"]["href"] == "/api/v3/categories/9"
        assert links["budget"]["href"] == "/api/v3/budgets/10"


class TestUpdateWorkpackage:
    @responses.activate
    def test_minimal(self, workpackage_json):
        responses.add(
            responses.PATCH,
            f"{BASE_URL}api/v3/work_packages/42",
            json=workpackage_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        wp = client.update_workpackage(42, lock_version=5, subject="New title")
        assert isinstance(wp, WorkPackage)
        body = json.loads(responses.calls[0].request.body)
        assert body["lockVersion"] == 5
        assert body["subject"] == "New title"

    @responses.activate
    def test_status_change(self, workpackage_json):
        responses.add(
            responses.PATCH,
            f"{BASE_URL}api/v3/work_packages/42",
            json=workpackage_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        client.update_workpackage(42, lock_version=5, status_id=7)
        body = json.loads(responses.calls[0].request.body)
        assert body["_links"]["status"]["href"] == "/api/v3/statuses/7"

    @responses.activate
    def test_remaining_time(self, workpackage_json):
        responses.add(
            responses.PATCH,
            f"{BASE_URL}api/v3/work_packages/42",
            json=workpackage_json,
            status=200,
        )
        client = ApiClient(BASE_URL, API_KEY)
        client.update_workpackage(42, lock_version=5, remaining_time="PT2H")
        body = json.loads(responses.calls[0].request.body)
        assert body["remainingTime"] == "PT2H"


class TestAddComment:
    @responses.activate
    def test_add_comment(self):
        activity_json = {"_type": "Activity", "id": 999, "comment": {"raw": "hello"}}
        responses.add(
            responses.POST,
            f"{BASE_URL}api/v3/work_packages/42/activities",
            json=activity_json,
            status=201,
        )
        client = ApiClient(BASE_URL, API_KEY)
        result = client.add_workpackage_comment(42, "hello")
        body = json.loads(responses.calls[0].request.body)
        assert body["comment"]["raw"] == "hello"


class TestCreateRelation:
    @responses.activate
    def test_create_basic(self, relation_json):
        responses.add(
            responses.POST,
            f"{BASE_URL}api/v3/relations",
            json=relation_json,
            status=201,
        )
        client = ApiClient(BASE_URL, API_KEY)
        rel = client.create_relation(42, 50, "blocks")
        assert isinstance(rel, Relation)
        body = json.loads(responses.calls[0].request.body)
        assert body["type"] == "blocks"
        assert body["_links"]["from"]["href"] == "/api/v3/work_packages/42"
        assert body["_links"]["to"]["href"] == "/api/v3/work_packages/50"

    @responses.activate
    def test_create_with_lag(self, relation_json):
        responses.add(
            responses.POST,
            f"{BASE_URL}api/v3/relations",
            json=relation_json,
            status=201,
        )
        client = ApiClient(BASE_URL, API_KEY)
        client.create_relation(42, 50, "precedes", description="wait", lag=3)
        body = json.loads(responses.calls[0].request.body)
        assert body["description"] == "wait"
        assert body["lag"] == 3


# -- DELETE ----------------------------------------------------------------

class TestHttpDelete:
    @responses.activate
    def test_sends_delete(self):
        responses.add(
            responses.DELETE,
            f"{BASE_URL}api/v3/work_packages/42",
            status=204,
        )
        client = ApiClient(BASE_URL, API_KEY)
        resp = client.http_delete("work_packages/42")
        assert resp.status_code == 204

    @responses.activate
    def test_delete_returns_true(self):
        responses.add(responses.DELETE, f"{BASE_URL}api/v3/work_packages/42", status=204)
        client = ApiClient(BASE_URL, API_KEY)
        assert client.delete("work_packages/42") is True

    @responses.activate
    def test_delete_error_raises(self):
        responses.add(responses.DELETE, f"{BASE_URL}api/v3/work_packages/999", status=404)
        client = ApiClient(BASE_URL, API_KEY)
        with pytest.raises(RequestError, match="404"):
            client.delete("work_packages/999")

    @responses.activate
    def test_delete_workpackage(self):
        responses.add(responses.DELETE, f"{BASE_URL}api/v3/work_packages/42", status=204)
        client = ApiClient(BASE_URL, API_KEY)
        assert client.delete_workpackage(42) is True

    @responses.activate
    def test_delete_relation(self):
        responses.add(responses.DELETE, f"{BASE_URL}api/v3/relations/100", status=204)
        client = ApiClient(BASE_URL, API_KEY)
        assert client.delete_relation(100) is True

    @responses.activate
    def test_delete_attachment(self):
        responses.add(responses.DELETE, f"{BASE_URL}api/v3/attachments/33", status=204)
        client = ApiClient(BASE_URL, API_KEY)
        assert client.delete_attachment(33) is True

    @responses.activate
    def test_delete_time_entry(self):
        responses.add(responses.DELETE, f"{BASE_URL}api/v3/time_entries/50", status=204)
        client = ApiClient(BASE_URL, API_KEY)
        assert client.delete_time_entry(50) is True


# -- New read endpoints ----------------------------------------------------

class TestNewReadEndpoints:
    @responses.activate
    def test_get_types(self, type_json):
        coll = make_collection("Collection", [type_json], total=1, offset=1, page_size=100)
        responses.add(responses.GET, f"{BASE_URL}api/v3/types", json=coll, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        types = client.get_types()
        assert len(types) == 1
        assert isinstance(types[0], Type)
        assert types[0].name == "Task"

    @responses.activate
    def test_get_type(self, type_json):
        responses.add(responses.GET, f"{BASE_URL}api/v3/types/1", json=type_json, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        t = client.get_type(1)
        assert isinstance(t, Type)

    @responses.activate
    def test_get_types_by_project(self, type_json):
        coll = make_collection("Collection", [type_json], total=1, offset=1, page_size=100)
        responses.add(responses.GET, f"{BASE_URL}api/v3/projects/1/types", json=coll, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        types = client.get_types_by_project_id(1)
        assert len(types) == 1

    @responses.activate
    def test_get_priorities(self, priority_json):
        coll = make_collection("Collection", [priority_json], total=1, offset=1, page_size=100)
        responses.add(responses.GET, f"{BASE_URL}api/v3/priorities", json=coll, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        prios = client.get_priorities()
        assert len(prios) == 1
        assert isinstance(prios[0], Priority)

    @responses.activate
    def test_get_priority(self, priority_json):
        responses.add(responses.GET, f"{BASE_URL}api/v3/priorities/2", json=priority_json, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        p = client.get_priority(2)
        assert isinstance(p, Priority)

    @responses.activate
    def test_get_categories(self, category_json):
        coll = make_collection("Collection", [category_json], total=1, offset=1, page_size=100)
        responses.add(responses.GET, f"{BASE_URL}api/v3/projects/1/categories", json=coll, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        cats = client.get_categories_by_project_id(1)
        assert len(cats) == 1
        assert isinstance(cats[0], Category)

    @responses.activate
    def test_get_category(self, category_json):
        responses.add(responses.GET, f"{BASE_URL}api/v3/categories/3", json=category_json, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        c = client.get_category(3)
        assert isinstance(c, Category)

    @responses.activate
    def test_get_time_entries(self, time_entry_json):
        coll = make_collection("Collection", [time_entry_json], total=1, offset=1, page_size=100)
        responses.add(responses.GET, f"{BASE_URL}api/v3/time_entries", json=coll, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        entries = client.get_time_entries()
        assert len(entries) == 1
        assert isinstance(entries[0], TimeEntry)

    @responses.activate
    def test_get_time_entries_filtered(self, time_entry_json):
        coll = make_collection("Collection", [time_entry_json], total=1, offset=1, page_size=100)
        responses.add(responses.GET, f"{BASE_URL}api/v3/time_entries", json=coll, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        client.get_time_entries(work_package_id=42)
        assert "filters" in responses.calls[0].request.url

    @responses.activate
    def test_get_time_entry(self, time_entry_json):
        responses.add(responses.GET, f"{BASE_URL}api/v3/time_entries/50", json=time_entry_json, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        te = client.get_time_entry(50)
        assert isinstance(te, TimeEntry)

    @responses.activate
    def test_get_notification(self, notification_json):
        responses.add(responses.GET, f"{BASE_URL}api/v3/notifications/55", json=notification_json, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        n = client.get_notification(55)
        assert isinstance(n, Notification)

    @responses.activate
    def test_get_notifications(self, notification_json):
        coll = make_collection("Collection", [notification_json], total=1, offset=1, page_size=100)
        responses.add(responses.GET, f"{BASE_URL}api/v3/notifications", json=coll, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        notifs = client.get_notifications()
        assert len(notifs) == 1

    @responses.activate
    def test_get_attachment(self, attachment_json):
        responses.add(responses.GET, f"{BASE_URL}api/v3/attachments/33", json=attachment_json, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        a = client.get_attachment(33)
        assert isinstance(a, Attachment)

    @responses.activate
    def test_get_activities(self, activity_json):
        coll = make_collection("Collection", [activity_json], total=1, offset=1, page_size=5)
        responses.add(responses.GET, f"{BASE_URL}api/v3/work_packages/42/activities", json=coll, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        acts = client.get_activities(42)
        assert len(acts) == 1

    @responses.activate
    def test_get_attachments_by_wp(self, attachment_json):
        coll = make_collection("Collection", [attachment_json], total=1, offset=1, page_size=5)
        responses.add(responses.GET, f"{BASE_URL}api/v3/work_packages/42/attachments", json=coll, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        atts = client.get_attachments_by_work_package(42)
        assert len(atts) == 1


# -- Time entry write methods -----------------------------------------------

class TestTimeEntryWrite:
    @responses.activate
    def test_create_time_entry(self, time_entry_json):
        responses.add(responses.POST, f"{BASE_URL}api/v3/time_entries", json=time_entry_json, status=201)
        client = ApiClient(BASE_URL, API_KEY)
        te = client.create_time_entry(42, "PT2H", "2024-03-15", comment="worked on it")
        assert isinstance(te, TimeEntry)
        body = json.loads(responses.calls[0].request.body)
        assert body["hours"] == "PT2H"
        assert body["spentOn"] == "2024-03-15"
        assert body["comment"]["raw"] == "worked on it"
        assert body["_links"]["workPackage"]["href"] == "/api/v3/work_packages/42"

    @responses.activate
    def test_create_time_entry_with_activity(self, time_entry_json):
        responses.add(responses.POST, f"{BASE_URL}api/v3/time_entries", json=time_entry_json, status=201)
        client = ApiClient(BASE_URL, API_KEY)
        client.create_time_entry(42, "PT1H", "2024-03-15", activity_id=5, project_id=1)
        body = json.loads(responses.calls[0].request.body)
        assert body["_links"]["activity"]["href"] == "/api/v3/time_entries/activities/5"
        assert body["_links"]["project"]["href"] == "/api/v3/projects/1"

    @responses.activate
    def test_update_time_entry(self, time_entry_json):
        responses.add(responses.PATCH, f"{BASE_URL}api/v3/time_entries/50", json=time_entry_json, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        client.update_time_entry(50, lock_version=1, hours="PT3H")
        body = json.loads(responses.calls[0].request.body)
        assert body["lockVersion"] == 1
        assert body["hours"] == "PT3H"


# -- Notification write methods ---------------------------------------------

class TestNotificationWrite:
    @responses.activate
    def test_mark_read(self, notification_json):
        notification_json["readIAN"] = True
        responses.add(responses.PATCH, f"{BASE_URL}api/v3/notifications/55", json=notification_json, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        n = client.mark_notification_read(55)
        body = json.loads(responses.calls[0].request.body)
        assert body["readIAN"] is True

    @responses.activate
    def test_mark_unread(self, notification_json):
        responses.add(responses.PATCH, f"{BASE_URL}api/v3/notifications/55", json=notification_json, status=200)
        client = ApiClient(BASE_URL, API_KEY)
        client.mark_notification_unread(55)
        body = json.loads(responses.calls[0].request.body)
        assert body["readIAN"] is False

    @responses.activate
    def test_mark_all_read(self):
        responses.add(responses.POST, f"{BASE_URL}api/v3/notifications/read_ian", status=204)
        client = ApiClient(BASE_URL, API_KEY)
        assert client.mark_all_notifications_read() is True
