# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Mounting of the demo routers.

The demo routers (counter, chatbot, ...) each build a local tracking client on ``~/.burr``,
so they are mounted only when ``BURR_SERVER_DEMOS`` asks for them: a plain ``burr`` server
exposes just the UI routes, and the ``burr-demo`` entry point turns the demos on.
"""

import importlib

import pytest
from click.testing import CliRunner

COUNTER_STATE_ROUTE = "/api/v0/counter/state/{project_id}/{app_id}"


@pytest.fixture
def run(monkeypatch):
    """The server module, imported with static serving off and a local backend configured."""
    monkeypatch.setenv("BURR_SERVE_STATIC", "false")
    monkeypatch.setenv("BURR_BACKEND_IMPL", "burr.tracking.server.backend.LocalBackend")
    return importlib.import_module("burr.tracking.server.run")


def _paths(app) -> set:
    return {route.path for route in app.routes}


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", " Yes "])
def test_demos_mounted_when_env_is_truthy(run, monkeypatch, value):
    monkeypatch.setenv("BURR_SERVER_DEMOS", value)
    app = run.create_burr_ui_app(serve_static=False)
    assert COUNTER_STATE_ROUTE in _paths(app)


@pytest.mark.parametrize("value", [None, "", "0", "false", "no", "off"])
def test_demos_not_mounted_otherwise(run, monkeypatch, value):
    if value is None:
        monkeypatch.delenv("BURR_SERVER_DEMOS", raising=False)
    else:
        monkeypatch.setenv("BURR_SERVER_DEMOS", value)
    app = run.create_burr_ui_app(serve_static=False)
    assert not any(path.startswith("/api/v0/counter") for path in _paths(app))
    assert "/api/v0/projects" in _paths(app)  # the UI's own routes are unaffected


def test_explicit_argument_overrides_env(run, monkeypatch):
    monkeypatch.delenv("BURR_SERVER_DEMOS", raising=False)
    assert COUNTER_STATE_ROUTE in _paths(
        run.create_burr_ui_app(serve_static=False, mount_demos=True)
    )
    monkeypatch.setenv("BURR_SERVER_DEMOS", "true")
    assert COUNTER_STATE_ROUTE not in _paths(
        run.create_burr_ui_app(serve_static=False, mount_demos=False)
    )


def test_demo_route_is_404_without_env_and_present_with_it(run, monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.delenv("BURR_SERVER_DEMOS", raising=False)
    client = TestClient(run.create_burr_ui_app(serve_static=False))
    assert client.get("/api/v0/counter/state/proj/app").status_code == 404
    assert client.get("/api/v0/projects").status_code == 200

    monkeypatch.setenv("BURR_SERVER_DEMOS", "true")
    client = TestClient(run.create_burr_ui_app(serve_static=False))
    # presence is checked through the schema so the demo's own storage is never touched
    assert COUNTER_STATE_ROUTE in client.get("/openapi.json").json()["paths"]


def test_mount_burr_ui_passes_the_flag_through(run, monkeypatch):
    from fastapi import FastAPI

    monkeypatch.delenv("BURR_SERVER_DEMOS", raising=False)
    parent = FastAPI()
    ui_app = run.mount_burr_ui(parent, serve_static=False)
    assert COUNTER_STATE_ROUTE not in _paths(ui_app)
    ui_app = run.mount_burr_ui(parent, path="/with-demos", serve_static=False, mount_demos=True)
    assert COUNTER_STATE_ROUTE in _paths(ui_app)


class TestCli:
    """``burr`` leaves the demos off; ``burr-demo`` turns them on through the environment."""

    def test_run_server_sets_the_flag_only_on_request(self, monkeypatch):
        cli_main = importlib.import_module("burr.cli.__main__")
        captured = {}

        def fake_command(command, capture_output, addl_env=None):
            captured.clear()
            captured.update(addl_env or {})

        monkeypatch.setattr(cli_main, "_command", fake_command)
        # no_open and no_copy_demo_data keep the call from opening a browser or copying data
        cli_main._run_server(7241, False, True, True)
        assert "BURR_SERVER_DEMOS" not in captured
        cli_main._run_server(7241, False, True, True, demos=True)
        assert captured["BURR_SERVER_DEMOS"] == "true"

    def test_commands_are_wired_to_the_flag(self, monkeypatch):
        cli_main = importlib.import_module("burr.cli.__main__")
        calls = []
        monkeypatch.setattr(cli_main, "_run_server", lambda *args, **kwargs: calls.append(kwargs))

        result = CliRunner().invoke(cli_main.cli, ["run-server", "--no-open"])
        assert result.exit_code == 0, result.output
        assert calls[-1].get("demos", False) is False

        result = CliRunner().invoke(cli_main.cli, ["demo-server"])
        assert result.exit_code == 0, result.output
        assert calls[-1]["demos"] is True

    def test_help_mentions_the_flag(self):
        cli_main = importlib.import_module("burr.cli.__main__")
        for command in ["run-server", "demo-server"]:
            result = CliRunner().invoke(cli_main.cli, [command, "--help"])
            assert result.exit_code == 0, result.output
            assert "BURR_SERVER_DEMOS" in result.output
