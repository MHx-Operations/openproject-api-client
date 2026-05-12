"""Tests for openproject_api_client.resources."""

import copy
import datetime

import pytest

from openproject_api_client.resources import (
    Activity,
    Attachment,
    Category,
    Collection,
    GenericType,
    Grid,
    GridWidget,
    Membership,
    Notification,
    PlaceholderUser,
    Priority,
    Project,
    Query,
    Relation,
    Status,
    TimeEntry,
    Type,
    User,
    Version,
    WorkPackage,
    WorkPackageCollection,
    _parse_href_id,
)
from tests.conftest import make_collection, make_wp_collection


# -- _parse_href_id --------------------------------------------------------

class TestParseHrefId:
    def test_parse_href_id_happy_paths(self):
        """Numeric path-style hrefs return the trailing integer."""
        assert _parse_href_id("/api/v3/projects/1") == 1
        assert _parse_href_id("/api/v3/work_packages/42") == 42
        # trailing-slash href: rstrip("/") must normalise it to return 123
        assert _parse_href_id("/api/v3/projects/123/") == 123

    def test_parse_href_id_returns_none_for_invalid(self):
        """All non-integer / non-path inputs return None."""
        # falsy inputs
        assert _parse_href_id(None) is None
        assert _parse_href_id("") is None
        # URN-style (undisclosed)
        assert _parse_href_id("urn:openproject-org:api:v3:undisclosed") is None
        # URN-style with numeric-looking trailing segment — still a URN
        assert _parse_href_id("urn:openproject:work_packages:42") is None
        # non-integer trailing segment
        assert _parse_href_id("/api/v3/projects/abc") is None
        # slug with no numeric end
        assert _parse_href_id("just-a-slug") is None
        # non-string input (e.g. int accidentally passed)
        assert _parse_href_id(42) is None


# -- GenericType -----------------------------------------------------------

class TestGenericType:
    def test_basic_attributes(self):
        obj = GenericType({"_type": "Foo", "id": 1, "name": "bar"})
        assert obj.id == 1
        assert obj.name == "bar"

    def test_underscore_keys_skipped_unless_debug(self):
        obj = GenericType({"_type": "Foo", "_links": {"self": "/x"}})
        assert not hasattr(obj, "_links")

    def test_debug_mode_keeps_underscore_keys(self):
        obj = GenericType({"_type": "Foo", "_links": {"self": "/x"}}, debug=True)
        assert hasattr(obj, "_links")
        assert hasattr(obj, "json")

    def test_datetime_parsing(self):
        obj = GenericType(
            {"_type": "X", "createdAt": "2024-01-15T10:00:00Z"},
            datetime_fields=["createdat"],
        )
        assert isinstance(obj.createdat, datetime.datetime)
        assert obj.createdat.year == 2024

    def test_date_parsing(self):
        obj = GenericType(
            {"_type": "X", "startDate": "2024-06-15"},
            date_fields=["startdate"],
        )
        assert isinstance(obj.startdate, datetime.datetime)
        assert obj.startdate.month == 6

    def test_invalid_datetime_stays_string(self):
        obj = GenericType(
            {"_type": "X", "createdAt": "not-a-date"},
            datetime_fields=["createdat"],
        )
        assert obj.createdat == "not-a-date"

    def test_none_datetime_stays_none(self):
        obj = GenericType(
            {"_type": "X", "createdAt": None},
            datetime_fields=["createdat"],
        )
        assert obj.createdat is None

    def test_str(self):
        obj = GenericType({"_type": "Foo", "id": 7})
        assert "7" in str(obj)


# -- Project ---------------------------------------------------------------

class TestProject:
    def test_from_json(self, project_json):
        p = Project(project_json)
        assert p.id == 1
        assert p.identifier == "my-project"
        assert p.name == "My Project"
        assert p.active is True
        assert isinstance(p.createdat, datetime.datetime)
        assert p.parent_id is None

    def test_favorited(self, project_json):
        p = Project(project_json)
        assert p.favorited is True

    def test_parent_from_links(self, child_project_json):
        p = Project(child_project_json)
        assert p.parent_id == 1

    def test_parent_from_embedded(self, child_project_json):
        # _embedded takes precedence since it's parsed first -- but _links
        # also sets it. Both should result in parent_id=1.
        p = Project(child_project_json)
        assert p.parent_id == 1

    def test_str(self, project_json):
        p = Project(project_json)
        assert "My Project" in str(p)

    def test_hierarchy_defaults(self, project_json):
        p = Project(project_json)
        assert p.path == []
        assert p.path_ids == []
        assert p.level == 1


# -- WorkPackage -----------------------------------------------------------

class TestWorkPackage:
    def test_from_json(self, workpackage_json):
        wp = WorkPackage(workpackage_json)
        assert wp.id == 42
        assert wp.subject == "Fix the widget"
        assert wp.type == "Bug"
        assert wp.type_id == 1
        assert wp.priority == "High"
        assert wp.priority_id == 2
        assert wp.status == "New"
        assert wp.status_id == 1
        assert wp.project == "My Project"
        assert wp.project_id == 1
        assert wp.author == "Alice"
        assert wp.author_id == 3
        assert wp.assignee == "Bob"
        assert wp.assignee_id == 4
        assert wp.responsible == "Carol"
        assert wp.responsible_id == 5
        assert wp.version == "v1.0"
        assert wp.version_id == 7
        assert wp.parent_id == 10

    def test_new_attributes(self, workpackage_json):
        wp = WorkPackage(workpackage_json)
        assert wp.readonly is False
        assert wp.derivedpercentagedone == 25
        assert wp.ignorenonworkingdays is False
        assert wp.spenttime == "PT5H"
        assert wp.duration == "P14D"
        assert wp.date is None
        assert wp.budget == "Q1 Budget"
        assert wp.budget_id == 8
        assert wp.category == "Backend"
        assert wp.category_id == 3

    def test_date_fields_parsed(self, workpackage_json):
        wp = WorkPackage(workpackage_json)
        assert isinstance(wp.startdate, datetime.datetime)
        assert wp.startdate.day == 1
        assert isinstance(wp.duedate, datetime.datetime)
        assert wp.duedate.day == 15
        assert isinstance(wp.derivedstartdate, datetime.datetime)
        assert isinstance(wp.derivedduedate, datetime.datetime)

    def test_embedded_budget_category(self, workpackage_json):
        """When _embedded contains budget/category, those override links."""
        wp_json = dict(workpackage_json)
        wp_json["_embedded"] = {
            "budget": {"id": 9, "subject": "Q2 Budget"},
            "category": {"id": 4, "name": "Frontend"},
        }
        wp = WorkPackage(wp_json)
        assert wp.budget == "Q2 Budget"
        assert wp.budget_id == 9
        assert wp.category == "Frontend"
        assert wp.category_id == 4

    def test_embedded_relations(self, workpackage_with_relations_json):
        wp = WorkPackage(workpackage_with_relations_json)
        assert len(wp.relations_obj) == 2

        # outbound: 42 -[blocks]-> 50
        assert "blocks" in wp.relations_out
        assert 50 in wp.relations_out["blocks"]

        # inbound: 30 -[relates]-> 42
        assert "relates" in wp.relations_in
        assert 30 in wp.relations_in["relates"]

    def test_update_relations(self, workpackage_json, relation_json):
        wp = WorkPackage(workpackage_json)
        assert wp.relations_obj == []

        rel = Relation(relation_json)
        wp.update_relations([rel])

        assert len(wp.relations_obj) == 1
        assert "blocks" in wp.relations_out
        assert 50 in wp.relations_out["blocks"]

    def test_update_relations_filters(self, workpackage_json):
        """Only relations involving this WP are kept."""
        wp = WorkPackage(workpackage_json)
        unrelated = Relation({
            "_type": "Relation", "id": 999,
            "name": "relates", "type": "relates", "reverseType": "relates",
            "description": "",
            "_links": {
                "from": {"href": "/api/v3/work_packages/80", "title": "X"},
                "to": {"href": "/api/v3/work_packages/90", "title": "Y"},
            },
        })
        wp.update_relations([unrelated])
        assert wp.relations_obj == []

    def test_str(self, workpackage_json):
        wp = WorkPackage(workpackage_json)
        assert "Fix the widget" in str(wp)

    def test_multiple_inbound_same_type_not_overwritten(self, workpackage_json):
        """Regression: multiple inbound relations of the same type must
        accumulate into a list, not silently overwrite each other."""
        wp_json = dict(workpackage_json)
        wp_json["_embedded"] = {
            "relations": {
                "_embedded": {
                    "elements": [
                        {
                            "_type": "Relation", "id": 200,
                            "name": "blocks", "type": "blocks",
                            "reverseType": "blocked", "description": "",
                            "_links": {
                                "from": {"href": "/api/v3/work_packages/10", "title": "A"},
                                "to": {"href": "/api/v3/work_packages/42", "title": "Fix the widget"},
                            },
                        },
                        {
                            "_type": "Relation", "id": 201,
                            "name": "blocks", "type": "blocks",
                            "reverseType": "blocked", "description": "",
                            "_links": {
                                "from": {"href": "/api/v3/work_packages/20", "title": "B"},
                                "to": {"href": "/api/v3/work_packages/42", "title": "Fix the widget"},
                            },
                        },
                    ]
                }
            }
        }
        wp = WorkPackage(wp_json)
        # Both inbound relations should be present under "blocked"
        assert "blocked" in wp.relations_in
        assert 10 in wp.relations_in["blocked"]
        assert 20 in wp.relations_in["blocked"]
        assert len(wp.relations_in["blocked"]) == 2

    def test_multiple_outbound_same_type_not_overwritten(self, workpackage_json):
        """Regression: multiple outbound relations of same type accumulate."""
        wp_json = dict(workpackage_json)
        wp_json["_embedded"] = {
            "relations": {
                "_embedded": {
                    "elements": [
                        {
                            "_type": "Relation", "id": 300,
                            "name": "blocks", "type": "blocks",
                            "reverseType": "blocked", "description": "",
                            "_links": {
                                "from": {"href": "/api/v3/work_packages/42", "title": "Fix the widget"},
                                "to": {"href": "/api/v3/work_packages/50", "title": "Deploy"},
                            },
                        },
                        {
                            "_type": "Relation", "id": 301,
                            "name": "blocks", "type": "blocks",
                            "reverseType": "blocked", "description": "",
                            "_links": {
                                "from": {"href": "/api/v3/work_packages/42", "title": "Fix the widget"},
                                "to": {"href": "/api/v3/work_packages/60", "title": "Release"},
                            },
                        },
                    ]
                }
            }
        }
        wp = WorkPackage(wp_json)
        assert "blocks" in wp.relations_out
        assert 50 in wp.relations_out["blocks"]
        assert 60 in wp.relations_out["blocks"]
        assert len(wp.relations_out["blocks"]) == 2

    def test_mixed_relation_directions(self, workpackage_json):
        """A relation where this WP is both from and to (different relations)
        results in correct in/out separation."""
        wp_json = dict(workpackage_json)
        wp_json["_embedded"] = {
            "relations": {
                "_embedded": {
                    "elements": [
                        {
                            "_type": "Relation", "id": 400,
                            "name": "blocks", "type": "blocks",
                            "reverseType": "blocked", "description": "",
                            "_links": {
                                "from": {"href": "/api/v3/work_packages/42", "title": "Fix"},
                                "to": {"href": "/api/v3/work_packages/50", "title": "Deploy"},
                            },
                        },
                        {
                            "_type": "Relation", "id": 401,
                            "name": "follows", "type": "follows",
                            "reverseType": "precedes", "description": "",
                            "_links": {
                                "from": {"href": "/api/v3/work_packages/30", "title": "Spec"},
                                "to": {"href": "/api/v3/work_packages/42", "title": "Fix"},
                            },
                        },
                    ]
                }
            }
        }
        wp = WorkPackage(wp_json)
        assert wp.relations_out == {"blocks": [50]}
        assert wp.relations_in == {"precedes": [30]}

    def test_embedded_overrides_links(self, workpackage_json):
        """When both _links and _embedded provide data, _embedded wins."""
        wp_json = dict(workpackage_json)
        wp_json["_embedded"] = {
            "status": {"name": "In Progress"},
            "project": {"name": "Other Project", "id": 99},
        }
        wp = WorkPackage(wp_json)
        assert wp.status == "In Progress"
        assert wp.project == "Other Project"
        assert wp.project_id == 99


# -- Relation --------------------------------------------------------------

class TestRelation:
    def test_from_json(self, relation_json):
        r = Relation(relation_json)
        assert r.id == 100
        assert r.type == "blocks"
        assert r.reversetype == "blocked"
        assert r.from_id == 42
        assert r.from_title == "Fix the widget"
        assert r.to_id == 50
        assert r.to_title == "Deploy"
        assert r.description == "blocker"

    def test_lag(self, relation_json):
        r = Relation(relation_json)
        assert r.lag == 2

    def test_lag_default_none(self):
        r = Relation({
            "_type": "Relation", "id": 1,
            "name": "relates", "type": "relates", "reverseType": "relates",
            "description": "",
            "_links": {
                "from": {"href": "/api/v3/work_packages/1", "title": "A"},
                "to": {"href": "/api/v3/work_packages/2", "title": "B"},
            },
        })
        assert r.lag is None

    def test_str(self, relation_json):
        r = Relation(relation_json)
        s = str(r)
        assert "42" in s
        assert "50" in s
        assert "blocks" in s


# -- Version ---------------------------------------------------------------

class TestVersion:
    def test_from_json(self, version_json):
        v = Version(version_json)
        assert v.id == 7
        assert v.name == "v1.0"
        assert v.status == "open"
        assert isinstance(v.startdate, datetime.datetime)
        assert isinstance(v.enddate, datetime.datetime)
        assert isinstance(v.createdat, datetime.datetime)

    def test_str(self, version_json):
        v = Version(version_json)
        assert "v1.0" in str(v)


# -- User ------------------------------------------------------------------

class TestUser:
    def test_from_json(self, user_json):
        u = User(user_json)
        assert u.id == 3
        assert u.login == "alice"
        assert u.firstname == "Alice"
        assert u.lastname == "Smith"
        assert u.name == "Alice Smith"
        assert u.email == "alice@example.com"

    def test_new_attributes(self, user_json):
        u = User(user_json)
        assert u.admin is False
        assert u.avatar == "https://op.example.com/avatars/3"
        assert u.status == "active"
        assert u.language == "en"

    def test_str(self, user_json):
        assert "Alice Smith" in str(User(user_json))


# -- PlaceholderUser -------------------------------------------------------

class TestPlaceholderUser:
    def test_from_json(self, placeholder_user_json):
        pu = PlaceholderUser(placeholder_user_json)
        assert pu.id == 10
        assert pu.name == "TBD Developer"

    def test_str(self, placeholder_user_json):
        assert "TBD Developer" in str(PlaceholderUser(placeholder_user_json))


# -- Membership ------------------------------------------------------------

class TestMembership:
    def test_from_json(self, membership_json):
        m = Membership(membership_json)
        assert m.id == 20
        assert m.project == "My Project"
        assert m.project_id == 1
        assert m.principal == "Alice Smith"
        assert m.principal_id == 3
        assert m.principal_type == "users"

    def test_roles(self, membership_json):
        m = Membership(membership_json)
        assert len(m.roles) == 2
        assert m.roles[0] == {"id": 5, "name": "Member"}
        assert m.roles[1] == {"id": 6, "name": "Developer"}

    def test_roles_empty_when_no_embedded(self):
        m = Membership({
            "_type": "Membership", "id": 21,
            "createdAt": "2024-01-01T00:00:00+00:00",
            "updatedAt": "2024-01-01T00:00:00+00:00",
            "_links": {
                "project": {"href": "/api/v3/projects/1", "title": "P"},
                "principal": {"href": "/api/v3/users/1", "title": "U"},
            },
        })
        assert m.roles == []

    def test_str(self, membership_json):
        s = str(Membership(membership_json))
        assert "Alice Smith" in s
        assert "My Project" in s


# -- Status ----------------------------------------------------------------

class TestStatus:
    def test_from_json(self, status_json):
        s = Status(status_json)
        assert s.id == 1
        assert s.name == "New"
        assert s.isclosed is False
        assert s.position == 1

    def test_new_attributes(self, status_json):
        s = Status(status_json)
        assert s.isdefault is True
        assert s.isreadonly is False
        assert s.excludedfromtotals is False
        assert s.defaultdoneratio == 0

    def test_str(self, status_json):
        assert "New" in str(Status(status_json))


# -- Grid / GridWidget -----------------------------------------------------

class TestGrid:
    def test_from_json(self, grid_json):
        g = Grid(grid_json)
        assert g.id == 5
        assert g.name == "My Board"
        assert g.rowcount == 4
        assert g.columncount == 3
        assert g.scope == "/projects/1/boards/5"
        assert g.widgets == []

    def test_str(self, grid_json):
        assert "My Board" in str(Grid(grid_json))

    def test_widgets_decoded(self, grid_json, grid_widget_json):
        grid_json["widgets"] = [grid_widget_json]
        g = Grid(grid_json)
        assert len(g.widgets) == 1
        assert isinstance(g.widgets[0], GridWidget)


class TestGridWidget:
    def test_from_json(self, grid_widget_json):
        gw = GridWidget(grid_widget_json)
        assert gw.id == 55
        assert gw.identifier == "work_package_query"
        assert gw.startrow == 1
        assert gw.endrow == 2

    def test_str(self, grid_widget_json):
        assert "work_package_query" in str(GridWidget(grid_widget_json))


# -- Query -----------------------------------------------------------------

class TestQuery:
    def test_from_json(self, query_json):
        q = Query(query_json)
        assert q.id == 99
        assert q.name == "Open Bugs"
        assert q.project == "My Project"
        assert q.project_id == 1
        assert q.user == "Alice Smith"
        assert q.user_id == 3
        assert q.public is True

    def test_timestamps(self, query_json):
        q = Query(query_json)
        assert q.timestamps == []

    def test_str(self, query_json):
        assert "Open Bugs" in str(Query(query_json))


# -- Collection / WorkPackageCollection ------------------------------------

class TestCollection:
    def test_iteration(self, status_json):
        coll_json = make_collection("Collection", [status_json], total=1)
        c = Collection(coll_json)
        items = list(c)
        assert len(items) == 1
        assert isinstance(items[0], Status)
        assert c.total == 1

    def test_empty_collection(self):
        coll_json = make_collection("Collection", [], total=0)
        c = Collection(coll_json)
        assert list(c) == []

    def test_str(self, status_json):
        coll_json = make_collection("Collection", [status_json], total=1)
        c = Collection(coll_json)
        assert "total=1" in str(c)

    def test_collection_missing_embedded(self):
        d = {"_type": "Collection", "total": 0, "count": 0, "offset": 1, "pageSize": 5}
        c = Collection(d)
        assert list(c) == []
        assert len(list(c)) == 0

    def test_collection_embedded_without_elements(self):
        d = {"_type": "Collection", "total": 0, "count": 0, "_embedded": {}}
        c = Collection(d)
        assert list(c) == []

    def test_collection_empty_elements_regression(self):
        d = {"_type": "Collection", "total": 0, "count": 0, "_embedded": {"elements": []}}
        c = Collection(d)
        assert list(c) == []

    def test_collection_items_default_is_list(self):
        c = Collection({"_type": "Collection"})
        assert isinstance(c._items, list)


class TestWorkPackageCollection:
    def test_is_collection(self, workpackage_json):
        coll_json = make_wp_collection([workpackage_json], total=1)
        wpc = WorkPackageCollection(coll_json)
        items = list(wpc)
        assert len(items) == 1
        assert isinstance(items[0], WorkPackage)


# -- Type ------------------------------------------------------------------

class TestType:
    def test_from_json(self, type_json):
        t = Type(type_json)
        assert t.id == 1
        assert t.name == "Task"
        assert t.color == "#1A67A3"
        assert t.position == 1
        assert t.isdefault is True
        assert t.ismilestone is False

    def test_str(self, type_json):
        assert "Task" in str(Type(type_json))


# -- Priority --------------------------------------------------------------

class TestPriority:
    def test_from_json(self, priority_json):
        p = Priority(priority_json)
        assert p.id == 2
        assert p.name == "High"
        assert p.color == "#FF0000"
        assert p.position == 2
        assert p.isactive is True
        assert p.isdefault is False

    def test_str(self, priority_json):
        assert "High" in str(Priority(priority_json))


# -- Category --------------------------------------------------------------

class TestCategory:
    def test_from_json(self, category_json):
        c = Category(category_json)
        assert c.id == 3
        assert c.name == "Backend"
        assert c.project == "My Project"
        assert c.project_id == 1
        assert c.defaultassignee == "Alice Smith"
        assert c.defaultassignee_id == 3

    def test_str(self, category_json):
        assert "Backend" in str(Category(category_json))


# -- TimeEntry -------------------------------------------------------------

class TestTimeEntry:
    def test_from_json(self, time_entry_json):
        te = TimeEntry(time_entry_json)
        assert te.id == 50
        assert te.hours == "PT2H"
        assert te.ongoing is False
        assert te.project == "My Project"
        assert te.project_id == 1
        assert te.workpackage == "Fix the widget"
        assert te.workpackage_id == 42
        assert te.user == "Alice Smith"
        assert te.user_id == 3
        assert te.activity == "Development"
        assert te.activity_id == 1

    def test_str(self, time_entry_json):
        s = str(TimeEntry(time_entry_json))
        assert "50" in s
        assert "42" in s


# -- Activity --------------------------------------------------------------

class TestActivity:
    def test_from_json(self, activity_json):
        a = Activity(activity_json)
        assert a.id == 200
        assert a.version == 3
        assert a.user == "Alice Smith"
        assert a.user_id == 3

    def test_str(self, activity_json):
        assert "Alice Smith" in str(Activity(activity_json))


# -- Attachment ------------------------------------------------------------

class TestAttachment:
    def test_from_json(self, attachment_json):
        a = Attachment(attachment_json)
        assert a.id == 33
        assert a.filename == "screenshot.png"
        assert a.filesize == 12345
        assert a.contenttype == "image/png"
        assert a.author == "Alice Smith"
        assert a.author_id == 3
        assert a.container_id == 42
        assert a.container_type == "work_packages"
        assert "screenshot.png" in a.download_url

    def test_str(self, attachment_json):
        assert "screenshot.png" in str(Attachment(attachment_json))


# -- Notification ----------------------------------------------------------

class TestNotification:
    def test_from_json(self, notification_json):
        n = Notification(notification_json)
        assert n.id == 55
        assert n.subject == "WP updated"
        assert n.reason == "assigned"
        assert n.readian is False
        assert n.project == "My Project"
        assert n.project_id == 1
        assert n.resource_id == 42
        assert n.resource_type == "work_packages"
        assert n.actor == "Alice Smith"
        assert n.actor_id == 3

    def test_str(self, notification_json):
        s = str(Notification(notification_json))
        assert "assigned" in s
