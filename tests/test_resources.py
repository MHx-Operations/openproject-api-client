"""Tests for openproject_api_client.resources."""

import datetime

import pytest

from openproject_api_client.resources import (
    Collection,
    GenericType,
    Grid,
    GridWidget,
    Membership,
    PlaceholderUser,
    Project,
    Query,
    Relation,
    Status,
    User,
    Version,
    WorkPackage,
    WorkPackageCollection,
)
from tests.conftest import make_collection, make_wp_collection


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

    def test_parent_from_links(self, child_project_json):
        p = Project(child_project_json)
        assert p.parent_id == 1

    def test_parent_from_embedded(self, child_project_json):
        # _embedded takes precedence since it's parsed first — but _links
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


class TestWorkPackageCollection:
    def test_is_collection(self, workpackage_json):
        coll_json = make_wp_collection([workpackage_json], total=1)
        wpc = WorkPackageCollection(coll_json)
        items = list(wpc)
        assert len(items) == 1
        assert isinstance(items[0], WorkPackage)
