"""Shared fixtures and sample JSON payloads for tests."""

import pytest


# -- Minimal JSON payloads matching OpenProject API v3 shape --

@pytest.fixture
def project_json():
    return {
        "_type": "Project",
        "id": 1,
        "identifier": "my-project",
        "name": "My Project",
        "active": True,
        "public": False,
        "description": {"format": "markdown", "raw": "desc", "html": "<p>desc</p>"},
        "createdAt": "2024-01-15T10:00:00+00:00",
        "updatedAt": "2024-06-20T14:30:00+00:00",
        "status": "on_track",
        "statusExplanation": {"format": "markdown", "raw": "", "html": ""},
        "_links": {
            "parent": {"href": None},
            "self": {"href": "/api/v3/projects/1"},
        },
        "_embedded": {},
    }


@pytest.fixture
def child_project_json():
    return {
        "_type": "Project",
        "id": 2,
        "identifier": "child-project",
        "name": "Child Project",
        "active": True,
        "public": False,
        "description": {"format": "markdown", "raw": "", "html": ""},
        "createdAt": "2024-02-01T08:00:00+00:00",
        "updatedAt": "2024-06-21T09:00:00+00:00",
        "status": "on_track",
        "statusExplanation": {"format": "markdown", "raw": "", "html": ""},
        "_links": {
            "parent": {"href": "/api/v3/projects/1"},
            "self": {"href": "/api/v3/projects/2"},
        },
        "_embedded": {
            "parent": {"id": 1, "name": "My Project"},
        },
    }


@pytest.fixture
def workpackage_json():
    return {
        "_type": "WorkPackage",
        "id": 42,
        "lockVersion": 5,
        "subject": "Fix the widget",
        "description": {"format": "markdown", "raw": "details", "html": "<p>details</p>"},
        "scheduleManually": False,
        "startDate": None,
        "dueDate": None,
        "derivedStartDate": None,
        "derivedDueDate": None,
        "estimatedTime": None,
        "derivedEstimatedTime": None,
        "percentageDone": 0,
        "createdAt": "2024-03-01T12:00:00+00:00",
        "updatedAt": "2024-03-05T15:00:00+00:00",
        "_links": {
            "parent": {"href": "/api/v3/work_packages/10"},
            "type": {"href": "/api/v3/types/1", "title": "Bug"},
            "priority": {"href": "/api/v3/priorities/2", "title": "High"},
            "status": {"href": "/api/v3/statuses/1", "title": "New"},
            "project": {"href": "/api/v3/projects/1", "title": "My Project"},
            "author": {"href": "/api/v3/users/3", "title": "Alice"},
            "assignee": {"href": "/api/v3/users/4", "title": "Bob"},
            "responsible": {"href": "/api/v3/users/5", "title": "Carol"},
            "version": {"href": "/api/v3/versions/7", "title": "v1.0"},
        },
        "_embedded": {},
    }


@pytest.fixture
def workpackage_with_relations_json():
    """Work package that has embedded relations."""
    return {
        "_type": "WorkPackage",
        "id": 42,
        "lockVersion": 5,
        "subject": "Fix the widget",
        "description": {"format": "markdown", "raw": "", "html": ""},
        "scheduleManually": False,
        "startDate": None,
        "dueDate": None,
        "derivedStartDate": None,
        "derivedDueDate": None,
        "estimatedTime": None,
        "derivedEstimatedTime": None,
        "percentageDone": 0,
        "createdAt": "2024-03-01T12:00:00+00:00",
        "updatedAt": "2024-03-05T15:00:00+00:00",
        "_links": {
            "parent": {"href": "/api/v3/work_packages/10"},
            "type": {"href": "/api/v3/types/1", "title": "Bug"},
            "priority": {"href": "/api/v3/priorities/2", "title": "High"},
            "status": {"href": "/api/v3/statuses/1", "title": "New"},
            "project": {"href": "/api/v3/projects/1", "title": "My Project"},
            "author": {"href": "/api/v3/users/3", "title": "Alice"},
            "assignee": {"href": "/api/v3/users/4", "title": "Bob"},
            "responsible": {"href": "/api/v3/users/5", "title": "Carol"},
            "version": {"href": "/api/v3/versions/7", "title": "v1.0"},
        },
        "_embedded": {
            "relations": {
                "_embedded": {
                    "elements": [
                        {
                            "_type": "Relation",
                            "id": 100,
                            "name": "blocks",
                            "type": "blocks",
                            "reverseType": "blocked",
                            "description": "",
                            "_links": {
                                "from": {"href": "/api/v3/work_packages/42", "title": "Fix the widget"},
                                "to": {"href": "/api/v3/work_packages/50", "title": "Deploy"},
                            },
                        },
                        {
                            "_type": "Relation",
                            "id": 101,
                            "name": "relates",
                            "type": "relates",
                            "reverseType": "relates",
                            "description": "",
                            "_links": {
                                "from": {"href": "/api/v3/work_packages/30", "title": "Spec"},
                                "to": {"href": "/api/v3/work_packages/42", "title": "Fix the widget"},
                            },
                        },
                    ]
                }
            }
        },
    }


@pytest.fixture
def relation_json():
    return {
        "_type": "Relation",
        "id": 100,
        "name": "blocks",
        "type": "blocks",
        "reverseType": "blocked",
        "description": "blocker",
        "_links": {
            "from": {"href": "/api/v3/work_packages/42", "title": "Fix the widget"},
            "to": {"href": "/api/v3/work_packages/50", "title": "Deploy"},
        },
    }


@pytest.fixture
def version_json():
    return {
        "_type": "Version",
        "id": 7,
        "name": "v1.0",
        "description": {"format": "markdown", "raw": "first release", "html": ""},
        "startDate": "2024-01-01",
        "endDate": "2024-06-30",
        "status": "open",
        "sharing": "none",
        "createdAt": "2024-01-01T00:00:00+00:00",
        "updatedAt": "2024-01-02T00:00:00+00:00",
    }


@pytest.fixture
def user_json():
    return {
        "_type": "User",
        "id": 3,
        "login": "alice",
        "firstName": "Alice",
        "lastName": "Smith",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "createdAt": "2023-01-01T00:00:00+00:00",
        "updatedAt": "2023-06-01T00:00:00+00:00",
    }


@pytest.fixture
def placeholder_user_json():
    return {
        "_type": "PlaceholderUser",
        "id": 10,
        "name": "TBD Developer",
        "createdAt": "2024-01-01T00:00:00+00:00",
        "updatedAt": "2024-01-02T00:00:00+00:00",
    }


@pytest.fixture
def membership_json():
    return {
        "_type": "Membership",
        "id": 20,
        "createdAt": "2024-01-01T00:00:00+00:00",
        "updatedAt": "2024-02-01T00:00:00+00:00",
        "_links": {
            "project": {"href": "/api/v3/projects/1", "title": "My Project"},
            "principal": {"href": "/api/v3/users/3", "title": "Alice Smith"},
        },
    }


@pytest.fixture
def status_json():
    return {
        "_type": "Status",
        "id": 1,
        "name": "New",
        "color": "#1A67A3",
        "isClosed": False,
        "position": 1,
        "createdAt": "2023-01-01T00:00:00+00:00",
        "updatedAt": "2023-01-01T00:00:00+00:00",
    }


@pytest.fixture
def grid_json():
    return {
        "_type": "Grid",
        "id": 5,
        "name": "My Board",
        "rowCount": 4,
        "columnCount": 3,
        "options": {},
        "widgets": [],
        "createdAt": "2024-01-01T00:00:00+00:00",
        "updatedAt": "2024-02-01T00:00:00+00:00",
        "_links": {
            "scope": {"href": "/projects/1/boards/5"},
        },
    }


@pytest.fixture
def grid_widget_json():
    return {
        "_type": "GridWidget",
        "id": 55,
        "startRow": 1,
        "endRow": 2,
        "startColumn": 1,
        "endColumn": 3,
        "identifier": "work_package_query",
        "options": {"queryId": 99},
    }


@pytest.fixture
def query_json():
    return {
        "_type": "Query",
        "id": 99,
        "name": "Open Bugs",
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
        "createdAt": "2024-01-01T00:00:00+00:00",
        "updatedAt": "2024-03-01T00:00:00+00:00",
        "_links": {
            "project": {"href": "/api/v3/projects/1", "title": "My Project"},
            "user": {"href": "/api/v3/users/3", "title": "Alice Smith"},
        },
        "_embedded": {},
    }


def make_collection(element_type, elements, total=None, offset=1, page_size=5):
    """Helper to build a Collection JSON envelope."""
    if total is None:
        total = len(elements)
    return {
        "_type": "Collection",
        "total": total,
        "count": len(elements),
        "offset": offset,
        "pageSize": page_size,
        "_embedded": {
            "elements": elements,
        },
    }


def make_wp_collection(elements, total=None, offset=1, page_size=5):
    """Helper to build a WorkPackageCollection JSON envelope."""
    coll = make_collection("WorkPackageCollection", elements, total, offset, page_size)
    coll["_type"] = "WorkPackageCollection"
    return coll
