"""Tests for the CLI module."""

import json
import os
from unittest import mock

import pytest

from openproject_api_client.cli import main, dispatch, json_out, text_out, _obj_to_dict, GUIDE_TEXT
from openproject_api_client.resources import (
    Project, WorkPackage, Relation, Version, User, PlaceholderUser,
    Membership, Status, Grid, Query,
)


# -- Helpers ---------------------------------------------------------------

def _env(**overrides):
    """Return a clean env dict with only the specified overrides."""
    base = {k: v for k, v in os.environ.items()
            if k not in ("OPENPROJECT_BASEURL", "OPENPROJECT_APIKEY")}
    base.update(overrides)
    return base


def _run_main(argv, env=None):
    """Run main() with patched sys.argv and environment."""
    if env is None:
        env = _env(OPENPROJECT_BASEURL="https://op.example.com/",
                    OPENPROJECT_APIKEY="test-key")
    with mock.patch.dict(os.environ, env, clear=True):
        with mock.patch("sys.argv", ["openproject-cli"] + argv):
            with mock.patch("openproject_api_client.cli.dispatch", return_value=None) as mock_dispatch:
                main()
                return mock_dispatch


# -- Arg parsing -----------------------------------------------------------

class TestCliArgParsing:
    def test_missing_baseurl_raises(self):
        with mock.patch.dict(os.environ, _env(), clear=True):
            with mock.patch("sys.argv", ["openproject-cli"]):
                with pytest.raises(Exception, match="base url"):
                    main()

    def test_missing_apikey_raises(self):
        with mock.patch.dict(os.environ, _env(OPENPROJECT_BASEURL="https://op.example.com"), clear=True):
            with mock.patch("sys.argv", ["openproject-cli"]):
                with pytest.raises(Exception, match="API key"):
                    main()

    def test_env_vars_used(self):
        env = _env(OPENPROJECT_BASEURL="https://op.example.com/", OPENPROJECT_APIKEY="test-key")
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", ["openproject-cli"]):
                main()

    def test_cli_args_override_env(self):
        env = _env(OPENPROJECT_BASEURL="https://wrong.example.com/", OPENPROJECT_APIKEY="wrong-key")
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", [
                "openproject-cli",
                "--baseurl", "https://right.example.com/",
                "--apikey", "right-key",
            ]):
                main()


# -- Guide -----------------------------------------------------------------

class TestGuide:
    def test_guide_prints_text(self, capsys):
        with mock.patch("sys.argv", ["openproject-cli", "guide"]):
            main()
        out = capsys.readouterr().out
        assert "SETUP" in out
        assert "READ COMMANDS" in out
        assert "WRITE COMMANDS" in out
        assert "TYPICAL AI-AGENT WORKFLOW" in out
        assert "RELATION TYPES" in out
        assert "TIME FORMAT" in out

    def test_guide_no_credentials_needed(self):
        """guide subcommand works without baseurl/apikey."""
        with mock.patch.dict(os.environ, _env(), clear=True):
            with mock.patch("sys.argv", ["openproject-cli", "guide"]):
                main()  # should not raise


# -- Subcommand routing (read) --------------------------------------------

class TestDispatchRead:
    """Test that dispatch() correctly routes to read client methods."""

    def _make_args(self, **kwargs):
        return mock.MagicMock(**kwargs)

    def test_projects(self):
        client = mock.MagicMock()
        client.get_projects.return_value = []
        result = dispatch(client, self._make_args(mode='projects'))
        client.get_projects.assert_called_once()
        assert result == []

    def test_work_packages_all(self):
        client = mock.MagicMock()
        client.get_workpackages.return_value = []
        args = self._make_args(mode='work-packages', query_id=None, project_id=None, status='all')
        result = dispatch(client, args)
        client.get_workpackages.assert_called_once_with(status='all')

    def test_work_packages_by_project(self):
        client = mock.MagicMock()
        client.get_workpackages_by_project_id.return_value = []
        args = self._make_args(mode='work-packages', query_id=None, project_id=5, status='open')
        result = dispatch(client, args)
        client.get_workpackages_by_project_id.assert_called_once_with(5, status='open')

    def test_work_packages_by_query(self):
        client = mock.MagicMock()
        client.get_workpackages_by_query_id.return_value = []
        args = self._make_args(mode='work-packages', query_id=99, project_id=None, status=None)
        result = dispatch(client, args)
        client.get_workpackages_by_query_id.assert_called_once_with(99)

    def test_work_package_single(self):
        client = mock.MagicMock()
        args = self._make_args(mode='work-package', id=42)
        dispatch(client, args)
        client.get_workpackage.assert_called_once_with(42)

    def test_relations(self):
        client = mock.MagicMock()
        client.get_relations.return_value = []
        dispatch(client, self._make_args(mode='relations'))
        client.get_relations.assert_called_once()

    def test_relation_single(self):
        client = mock.MagicMock()
        args = self._make_args(mode='relation', id=100)
        dispatch(client, args)
        client.get_relation.assert_called_once_with(100)

    def test_versions(self):
        client = mock.MagicMock()
        client.get_versions.return_value = []
        dispatch(client, self._make_args(mode='versions'))
        client.get_versions.assert_called_once()

    def test_version_single(self):
        client = mock.MagicMock()
        args = self._make_args(mode='version', id=7)
        dispatch(client, args)
        client.get_version.assert_called_once_with(7)

    def test_users(self):
        client = mock.MagicMock()
        client.get_users.return_value = []
        dispatch(client, self._make_args(mode='users'))
        client.get_users.assert_called_once()

    def test_user_single(self):
        client = mock.MagicMock()
        args = self._make_args(mode='user', id=3)
        dispatch(client, args)
        client.get_user.assert_called_once_with(3)

    def test_placeholder_users(self):
        client = mock.MagicMock()
        client.get_placeholder_users.return_value = []
        dispatch(client, self._make_args(mode='placeholder-users'))
        client.get_placeholder_users.assert_called_once()

    def test_placeholder_user_single(self):
        client = mock.MagicMock()
        args = self._make_args(mode='placeholder-user', id=10)
        dispatch(client, args)
        client.get_placeholder_user.assert_called_once_with(10)

    def test_memberships(self):
        client = mock.MagicMock()
        client.get_project_members.return_value = []
        dispatch(client, self._make_args(mode='memberships'))
        client.get_project_members.assert_called_once()

    def test_membership_single(self):
        client = mock.MagicMock()
        args = self._make_args(mode='membership', id=20)
        dispatch(client, args)
        client.get_project_member.assert_called_once_with(20)

    def test_statuses(self):
        client = mock.MagicMock()
        client.get_statuses.return_value = []
        dispatch(client, self._make_args(mode='statuses'))
        client.get_statuses.assert_called_once()

    def test_status_single(self):
        client = mock.MagicMock()
        args = self._make_args(mode='status', id=1)
        dispatch(client, args)
        client.get_status.assert_called_once_with(1)

    def test_grids(self):
        client = mock.MagicMock()
        client.get_grids.return_value = []
        args = self._make_args(mode='grids', scope=None)
        dispatch(client, args)
        client.get_grids.assert_called_once_with(scope=None)

    def test_grids_with_scope(self):
        client = mock.MagicMock()
        client.get_grids.return_value = []
        args = self._make_args(mode='grids', scope='/projects/1/boards')
        dispatch(client, args)
        client.get_grids.assert_called_once_with(scope='/projects/1/boards')

    def test_grid_single(self):
        client = mock.MagicMock()
        args = self._make_args(mode='grid', id=5)
        dispatch(client, args)
        client.get_grid.assert_called_once_with(5)

    def test_query_single(self):
        client = mock.MagicMock()
        args = self._make_args(mode='query', id=99)
        dispatch(client, args)
        client.get_query.assert_called_once_with(99)

    def test_no_mode_returns_none(self):
        client = mock.MagicMock()
        result = dispatch(client, self._make_args(mode=None))
        assert result is None

    def test_types(self):
        client = mock.MagicMock()
        client.get_types.return_value = []
        dispatch(client, self._make_args(mode='types', project_id=None))
        client.get_types.assert_called_once()

    def test_types_by_project(self):
        client = mock.MagicMock()
        client.get_types_by_project_id.return_value = []
        dispatch(client, self._make_args(mode='types', project_id=5))
        client.get_types_by_project_id.assert_called_once_with(5)

    def test_type_single(self):
        client = mock.MagicMock()
        dispatch(client, self._make_args(mode='type', id=1))
        client.get_type.assert_called_once_with(1)

    def test_priorities(self):
        client = mock.MagicMock()
        client.get_priorities.return_value = []
        dispatch(client, self._make_args(mode='priorities'))
        client.get_priorities.assert_called_once()

    def test_priority_single(self):
        client = mock.MagicMock()
        dispatch(client, self._make_args(mode='priority', id=2))
        client.get_priority.assert_called_once_with(2)

    def test_categories(self):
        client = mock.MagicMock()
        client.get_categories_by_project_id.return_value = []
        dispatch(client, self._make_args(mode='categories', project_id=1))
        client.get_categories_by_project_id.assert_called_once_with(1)

    def test_category_single(self):
        client = mock.MagicMock()
        dispatch(client, self._make_args(mode='category', id=3))
        client.get_category.assert_called_once_with(3)

    def test_time_entries(self):
        client = mock.MagicMock()
        client.get_time_entries.return_value = []
        dispatch(client, self._make_args(mode='time-entries', work_package_id=None, project_id=None))
        client.get_time_entries.assert_called_once()

    def test_time_entry_single(self):
        client = mock.MagicMock()
        dispatch(client, self._make_args(mode='time-entry', id=50))
        client.get_time_entry.assert_called_once_with(50)

    def test_activities(self):
        client = mock.MagicMock()
        client.get_activities.return_value = []
        dispatch(client, self._make_args(mode='activities', id=42))
        client.get_activities.assert_called_once_with(42)

    def test_attachments(self):
        client = mock.MagicMock()
        client.get_attachments_by_work_package.return_value = []
        dispatch(client, self._make_args(mode='attachments', id=42))
        client.get_attachments_by_work_package.assert_called_once_with(42)

    def test_attachment_single(self):
        client = mock.MagicMock()
        dispatch(client, self._make_args(mode='attachment', id=33))
        client.get_attachment.assert_called_once_with(33)

    def test_notifications(self):
        client = mock.MagicMock()
        client.get_notifications.return_value = []
        dispatch(client, self._make_args(mode='notifications'))
        client.get_notifications.assert_called_once()

    def test_notification_single(self):
        client = mock.MagicMock()
        dispatch(client, self._make_args(mode='notification', id=55))
        client.get_notification.assert_called_once_with(55)


# -- Subcommand routing (write) --------------------------------------------

class TestDispatchWrite:
    """Test that dispatch() correctly routes to write client methods."""

    def _make_args(self, **kwargs):
        return mock.MagicMock(**kwargs)

    def test_create_work_package(self):
        client = mock.MagicMock()
        args = self._make_args(
            mode='create-work-package', project_id=1, subject="New WP",
            type_id=2, status_id=3, assignee_id=4, responsible_id=5,
            priority_id=6, version_id=7, parent_id=8, category_id=9,
            budget_id=10, start_date="2024-01-01", due_date="2024-02-01",
            estimated_time="PT8H", percentage_done=50,
            description="desc", schedule_manually=True,
        )
        dispatch(client, args)
        client.create_workpackage.assert_called_once_with(
            project_id=1, subject="New WP",
            type_id=2, status_id=3, assignee_id=4, responsible_id=5,
            priority_id=6, version_id=7, parent_id=8, category_id=9,
            budget_id=10, start_date="2024-01-01", due_date="2024-02-01",
            estimated_time="PT8H", percentage_done=50,
            description="desc", schedule_manually=True,
        )

    def test_update_work_package_fetches_lock_version(self):
        client = mock.MagicMock()
        mock_wp = mock.MagicMock()
        mock_wp.lockversion = 5
        client.get_workpackage.return_value = mock_wp
        args = self._make_args(
            mode='update-work-package', id=42,
            subject="Updated", type_id=None, status_id=7,
            assignee_id=None, responsible_id=None,
            priority_id=None, version_id=None, parent_id=None,
            category_id=None, budget_id=None,
            start_date=None, due_date=None,
            estimated_time=None, remaining_time=None,
            percentage_done=None, description=None,
            schedule_manually=None,
        )
        dispatch(client, args)
        client.get_workpackage.assert_called_once_with(42)
        client.update_workpackage.assert_called_once_with(
            workpackage_id=42, lock_version=5,
            subject="Updated", type_id=None, status_id=7,
            assignee_id=None, responsible_id=None,
            priority_id=None, version_id=None, parent_id=None,
            category_id=None, budget_id=None,
            start_date=None, due_date=None,
            estimated_time=None, remaining_time=None,
            percentage_done=None, description=None,
            schedule_manually=None,
        )

    def test_add_comment(self):
        client = mock.MagicMock()
        args = self._make_args(mode='add-comment', id=42, message="Status update")
        dispatch(client, args)
        client.add_workpackage_comment.assert_called_once_with(42, "Status update")

    def test_create_relation(self):
        client = mock.MagicMock()
        args = self._make_args(
            mode='create-relation',
            from_id=42, to_id=50, relation_type='blocks',
            description="reason", lag=2,
        )
        dispatch(client, args)
        client.create_relation.assert_called_once_with(
            from_id=42, to_id=50, relation_type='blocks',
            description="reason", lag=2,
        )

    def test_create_time_entry(self):
        client = mock.MagicMock()
        args = self._make_args(
            mode='create-time-entry',
            work_package_id=42, hours="PT2H", spent_on="2024-03-15",
            activity_id=1, comment="worked", project_id=1,
        )
        dispatch(client, args)
        client.create_time_entry.assert_called_once_with(
            work_package_id=42, hours="PT2H", spent_on="2024-03-15",
            activity_id=1, comment="worked", project_id=1,
        )

    def test_update_time_entry_fetches_lock_version(self):
        client = mock.MagicMock()
        mock_te = mock.MagicMock()
        mock_te.lockversion = 1
        client.get_time_entry.return_value = mock_te
        args = self._make_args(
            mode='update-time-entry', id=50,
            hours="PT3H", spent_on=None, activity_id=None, comment=None,
        )
        dispatch(client, args)
        client.get_time_entry.assert_called_once_with(50)
        client.update_time_entry.assert_called_once()

    def test_mark_notification_read(self):
        client = mock.MagicMock()
        dispatch(client, self._make_args(mode='mark-notification-read', id=55))
        client.mark_notification_read.assert_called_once_with(55)

    def test_mark_notification_unread(self):
        client = mock.MagicMock()
        dispatch(client, self._make_args(mode='mark-notification-unread', id=55))
        client.mark_notification_unread.assert_called_once_with(55)

    def test_mark_all_notifications_read(self):
        client = mock.MagicMock()
        dispatch(client, self._make_args(mode='mark-all-notifications-read'))
        client.mark_all_notifications_read.assert_called_once()

    def test_delete_work_package(self):
        client = mock.MagicMock()
        client.delete_workpackage.return_value = True
        result = dispatch(client, self._make_args(mode='delete-work-package', id=42))
        client.delete_workpackage.assert_called_once_with(42)
        assert result is True

    def test_delete_relation(self):
        client = mock.MagicMock()
        client.delete_relation.return_value = True
        result = dispatch(client, self._make_args(mode='delete-relation', id=100))
        client.delete_relation.assert_called_once_with(100)
        assert result is True

    def test_delete_time_entry(self):
        client = mock.MagicMock()
        client.delete_time_entry.return_value = True
        result = dispatch(client, self._make_args(mode='delete-time-entry', id=50))
        client.delete_time_entry.assert_called_once_with(50)

    def test_delete_attachment(self):
        client = mock.MagicMock()
        client.delete_attachment.return_value = True
        result = dispatch(client, self._make_args(mode='delete-attachment', id=33))
        client.delete_attachment.assert_called_once_with(33)


# -- Output formatting -----------------------------------------------------

class TestTextOut:
    def test_single_item(self, capsys):
        text_out("hello")
        assert capsys.readouterr().out.strip() == "hello"

    def test_list_items(self, capsys):
        text_out(["one", "two", "three"])
        out = capsys.readouterr().out
        assert "one" in out
        assert "two" in out
        assert "three" in out

    def test_resource_uses_str(self, capsys, project_json):
        p = Project(project_json)
        text_out(p)
        out = capsys.readouterr().out
        assert "My Project" in out

    def test_list_of_resources(self, capsys, status_json):
        s = Status(status_json)
        text_out([s, s])
        out = capsys.readouterr().out
        assert out.count("New") == 2


class TestJsonOut:
    def test_json_output(self, capsys):
        data = {"name": "test", "value": 42}
        json_out(data)
        captured = capsys.readouterr()
        assert '"name": "test"' in captured.out
        assert '"value": 42' in captured.out

    def test_json_out_with_objects(self, capsys):
        class Dummy:
            def __init__(self):
                self.x = 1
                self.y = "hello"

        json_out(Dummy())
        captured = capsys.readouterr()
        assert '"x": 1' in captured.out
        assert '"y": "hello"' in captured.out

    def test_json_out_list(self, capsys, status_json):
        s = Status(status_json)
        json_out([s])
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert isinstance(parsed, list)
        assert parsed[0]["name"] == "New"

    def test_json_out_single_resource(self, capsys, user_json):
        u = User(user_json)
        json_out(u)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["login"] == "alice"
        assert parsed["admin"] is False

    def test_json_filters_private_attrs(self, capsys, project_json):
        p = Project(project_json)
        json_out(p)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "_type" not in parsed
        assert "_GenericType__type" not in parsed


class TestObjToDict:
    def test_dict_passthrough(self):
        d = {"a": 1}
        assert _obj_to_dict(d) == {"a": 1}

    def test_filters_private(self):
        class Obj:
            def __init__(self):
                self.public = "yes"
                self._private = "no"
        result = _obj_to_dict(Obj())
        assert "public" in result
        assert "_private" not in result

    def test_nested_list(self):
        class Inner:
            def __init__(self):
                self.val = 42
        class Outer:
            def __init__(self):
                self.items = [Inner()]
        result = _obj_to_dict(Outer())
        assert result["items"][0]["val"] == 42


# -- Integration: main with subcommands -----------------------------------

class TestMainIntegration:
    """Test main() end-to-end with mocked ApiClient."""

    def _patch_and_run(self, argv, mock_client_method, return_value, json_flag=False):
        env = _env(OPENPROJECT_BASEURL="https://op.example.com/",
                    OPENPROJECT_APIKEY="test-key")
        cmd = ["openproject-cli"]
        if json_flag:
            cmd.append("--json")
        cmd.extend(argv)

        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", cmd):
                with mock.patch("openproject_api_client.ApiClient") as MockClient:
                    instance = MockClient.return_value
                    getattr(instance, mock_client_method).return_value = return_value
                    main()
                    return instance

    def test_projects_text(self, capsys):
        self._patch_and_run(["projects"], "get_projects", ["Project A", "Project B"])
        out = capsys.readouterr().out
        assert "Project A" in out
        assert "Project B" in out

    def test_projects_json(self, capsys):
        self._patch_and_run(["projects"], "get_projects", [{"name": "P1"}], json_flag=True)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed[0]["name"] == "P1"

    def test_statuses_text(self, capsys):
        self._patch_and_run(["statuses"], "get_statuses", ["New", "Closed"])
        out = capsys.readouterr().out
        assert "New" in out

    def test_user_single(self, capsys):
        self._patch_and_run(["user", "3"], "get_user", "User(3): Alice")
        out = capsys.readouterr().out
        assert "Alice" in out

    def test_version_single(self, capsys):
        self._patch_and_run(["version", "7"], "get_version", "Version(7): v1.0")
        out = capsys.readouterr().out
        assert "v1.0" in out

    def test_work_package_single(self, capsys):
        self._patch_and_run(["work-package", "42"], "get_workpackage", "WP(42): Fix it")
        out = capsys.readouterr().out
        assert "Fix it" in out

    def test_relation_single(self, capsys):
        self._patch_and_run(["relation", "100"], "get_relation", "Relation(100)")
        out = capsys.readouterr().out
        assert "100" in out

    def test_membership_single(self, capsys):
        self._patch_and_run(["membership", "20"], "get_project_member", "Membership(20)")
        out = capsys.readouterr().out
        assert "20" in out

    def test_grid_single(self, capsys):
        self._patch_and_run(["grid", "5"], "get_grid", "Grid(5)")
        out = capsys.readouterr().out
        assert "5" in out

    def test_query_single(self, capsys):
        self._patch_and_run(["query", "99"], "get_query", "Query(99)")
        out = capsys.readouterr().out
        assert "99" in out

    def test_no_subcommand_no_output(self, capsys):
        env = _env(OPENPROJECT_BASEURL="https://op.example.com/",
                    OPENPROJECT_APIKEY="test-key")
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", ["openproject-cli"]):
                with mock.patch("openproject_api_client.ApiClient"):
                    main()
        out = capsys.readouterr().out
        assert out == ""

    def test_api_error_exits_nonzero(self):
        import openproject_api_client as opc
        env = _env(OPENPROJECT_BASEURL="https://op.example.com/",
                    OPENPROJECT_APIKEY="test-key")
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", ["openproject-cli", "projects"]):
                with mock.patch("openproject_api_client.ApiClient") as MockClient:
                    MockClient.return_value.get_projects.side_effect = opc.ApiError("fail")
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    assert exc_info.value.code == 1

    def test_request_error_exits_nonzero(self):
        import openproject_api_client as opc
        env = _env(OPENPROJECT_BASEURL="https://op.example.com/",
                    OPENPROJECT_APIKEY="test-key")
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", ["openproject-cli", "projects"]):
                with mock.patch("openproject_api_client.ApiClient") as MockClient:
                    MockClient.return_value.get_projects.side_effect = opc.RequestError("fail")
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    assert exc_info.value.code == 1


# -- Write integration tests -----------------------------------------------

class TestMainWriteIntegration:
    def test_create_work_package(self, capsys):
        env = _env(OPENPROJECT_BASEURL="https://op.example.com/",
                    OPENPROJECT_APIKEY="test-key")
        cmd = ["openproject-cli", "create-work-package",
               "--project-id", "1", "--subject", "New task", "--status-id", "3"]
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", cmd):
                with mock.patch("openproject_api_client.ApiClient") as MockClient:
                    instance = MockClient.return_value
                    instance.create_workpackage.return_value = "WP(99): New task"
                    main()
                    instance.create_workpackage.assert_called_once()
                    call_kwargs = instance.create_workpackage.call_args
                    assert call_kwargs.kwargs['project_id'] == 1
                    assert call_kwargs.kwargs['subject'] == "New task"
                    assert call_kwargs.kwargs['status_id'] == 3
        out = capsys.readouterr().out
        assert "New task" in out

    def test_update_work_package(self, capsys):
        env = _env(OPENPROJECT_BASEURL="https://op.example.com/",
                    OPENPROJECT_APIKEY="test-key")
        cmd = ["openproject-cli", "update-work-package", "42", "--status-id", "7"]
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", cmd):
                with mock.patch("openproject_api_client.ApiClient") as MockClient:
                    instance = MockClient.return_value
                    mock_wp = mock.MagicMock()
                    mock_wp.lockversion = 5
                    instance.get_workpackage.return_value = mock_wp
                    instance.update_workpackage.return_value = "WP(42): Updated"
                    main()
                    instance.get_workpackage.assert_called_once_with(42)
                    call_kwargs = instance.update_workpackage.call_args.kwargs
                    assert call_kwargs['workpackage_id'] == 42
                    assert call_kwargs['lock_version'] == 5
                    assert call_kwargs['status_id'] == 7

    def test_add_comment(self, capsys):
        env = _env(OPENPROJECT_BASEURL="https://op.example.com/",
                    OPENPROJECT_APIKEY="test-key")
        cmd = ["openproject-cli", "add-comment", "42", "--message", "Done"]
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", cmd):
                with mock.patch("openproject_api_client.ApiClient") as MockClient:
                    instance = MockClient.return_value
                    instance.add_workpackage_comment.return_value = "Activity(1)"
                    main()
                    instance.add_workpackage_comment.assert_called_once_with(42, "Done")

    def test_create_relation(self, capsys):
        env = _env(OPENPROJECT_BASEURL="https://op.example.com/",
                    OPENPROJECT_APIKEY="test-key")
        cmd = ["openproject-cli", "create-relation",
               "--from-id", "42", "--to-id", "50", "--type", "blocks"]
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", cmd):
                with mock.patch("openproject_api_client.ApiClient") as MockClient:
                    instance = MockClient.return_value
                    instance.create_relation.return_value = "Relation(100)"
                    main()
                    instance.create_relation.assert_called_once_with(
                        from_id=42, to_id=50, relation_type='blocks',
                        description=None, lag=None,
                    )
