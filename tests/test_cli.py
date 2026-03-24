"""Tests for the CLI module."""

import os
from unittest import mock

import pytest

from openproject_api_client.cli import main, json_out


class TestCliArgParsing:
    def test_missing_baseurl_raises(self):
        """CLI raises when no base URL is provided via arg or env."""
        with mock.patch.dict(os.environ, {}, clear=True):
            env = {k: v for k, v in os.environ.items()
                   if k not in ("OPENPROJECT_BASEURL", "OPENPROJECT_APIKEY")}
            with mock.patch.dict(os.environ, env, clear=True):
                with mock.patch("sys.argv", ["openproject-cli"]):
                    with pytest.raises(Exception, match="base url"):
                        main()

    def test_missing_apikey_raises(self):
        """CLI raises when no API key is provided via arg or env."""
        env = {k: v for k, v in os.environ.items()
               if k not in ("OPENPROJECT_BASEURL", "OPENPROJECT_APIKEY")}
        env["OPENPROJECT_BASEURL"] = "https://op.example.com"
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", ["openproject-cli"]):
                with pytest.raises(Exception, match="API key"):
                    main()

    def test_env_vars_used(self):
        """CLI picks up base URL and API key from environment."""
        env = {k: v for k, v in os.environ.items()
               if k not in ("OPENPROJECT_BASEURL", "OPENPROJECT_APIKEY")}
        env["OPENPROJECT_BASEURL"] = "https://op.example.com/"
        env["OPENPROJECT_APIKEY"] = "test-key"
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", ["openproject-cli"]):
                # Should not raise — the skeleton just passes
                main()

    def test_cli_args_override_env(self):
        """--baseurl and --apikey override env vars."""
        env = {k: v for k, v in os.environ.items()
               if k not in ("OPENPROJECT_BASEURL", "OPENPROJECT_APIKEY")}
        env["OPENPROJECT_BASEURL"] = "https://wrong.example.com/"
        env["OPENPROJECT_APIKEY"] = "wrong-key"
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("sys.argv", [
                "openproject-cli",
                "--baseurl", "https://right.example.com/",
                "--apikey", "right-key",
            ]):
                # Should not raise
                main()


class TestJsonOut:
    def test_json_output(self, capsys):
        """json_out prints formatted JSON."""
        data = {"name": "test", "value": 42}
        json_out(data)
        captured = capsys.readouterr()
        assert '"name": "test"' in captured.out
        assert '"value": 42' in captured.out

    def test_json_out_with_objects(self, capsys):
        """json_out handles objects via __dict__ fallback."""
        class Dummy:
            def __init__(self):
                self.x = 1
                self.y = "hello"

        json_out(Dummy())
        captured = capsys.readouterr()
        assert '"x": 1' in captured.out
        assert '"y": "hello"' in captured.out
