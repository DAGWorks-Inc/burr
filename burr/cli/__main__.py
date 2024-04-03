import json
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from contextlib import contextmanager
from importlib.resources import files

from burr import telemetry
from burr.core.persistence import PersistedStateData
from burr.integrations.base import require_plugin

try:
    import click
    import requests
    from loguru import logger
except ImportError as e:
    require_plugin(
        e,
        ["click", "requests", "loguru"],
        "start",
    )


# TODO -- add this as a general callback to the CLI
def _telemetry_if_enabled(event: str):
    if telemetry.is_telemetry_enabled():
        telemetry.create_and_send_cli_event(event)


def _command(command: str, capture_output: bool) -> str:
    """Runs a simple command"""
    logger.info(f"Running command: {command}")
    if isinstance(command, str):
        command = command.split(" ")
        if capture_output:
            try:
                return (
                    subprocess.check_output(command, stderr=subprocess.PIPE, shell=False)
                    .decode()
                    .strip()
                )
            except subprocess.CalledProcessError as e:
                print(e.stdout.decode())
                print(e.stderr.decode())
                raise e
        subprocess.run(command, shell=False, check=True)


def _get_git_root() -> str:
    return _command("git rev-parse --show-toplevel", capture_output=True)


def open_when_ready(check_url: str, open_url: str):
    while True:
        try:
            response = requests.get(check_url)
            if response.status_code == 200:
                webbrowser.open(open_url)
                return
            else:
                pass
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)


@contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


@click.group()
def cli():
    pass


def _build_ui():
    cmd = "npm run build --prefix telemetry/ui"
    _command(cmd, capture_output=False)
    # create a symlink so we can get packages inside it...
    cmd = "rm -rf burr/tracking/server/build"
    _command(cmd, capture_output=False)
    cmd = "cp -R telemetry/ui/build burr/tracking/server/build"
    _command(cmd, capture_output=False)


@cli.command()
def build_ui():
    git_root = _get_git_root()
    with cd(git_root):
        _build_ui()


def _run_server(port: int, dev_mode: bool, no_open: bool, no_copy_demo_data: bool, initial_page=""):
    _telemetry_if_enabled("run_server")
    # TODO: Implement server running logic here
    # Example: Start a web server, configure ports, etc.
    logger.info(f"Starting server on port {port}")
    cmd = f"uvicorn burr.tracking.server.run:app --port {port}"
    if dev_mode:
        cmd += " --reload"
    base_dir = os.path.expanduser("~/.burr")
    if not no_copy_demo_data:
        logger.info(f"Copying demo data over to {base_dir}...")
        demo_data_path = files("burr").joinpath("tracking/server/demo_data")
        for top_level in os.listdir(demo_data_path):
            if not os.path.exists(f"{base_dir}/{top_level}"):
                logger.info(f"Copying {top_level} over...")
                shutil.copytree(f"{demo_data_path}/{top_level}", f"{base_dir}/{top_level}")

    if not no_open:
        thread = threading.Thread(
            target=open_when_ready,
            kwargs={
                "open_url": (open_url := f"http://localhost:{port}/{initial_page}"),
                "check_url": f"{open_url}/ready",
            },
            daemon=True,
        )
        thread.start()
    _command(cmd, capture_output=False)


@cli.command()
@click.option("--port", default=7241, help="Port to run the server on")
@click.option("--dev-mode", is_flag=True, help="Run the server in development mode")
@click.option("--no-open", is_flag=True, help="Run the server without opening it")
@click.option("--no-copy-demo_data", is_flag=True, help="Don't copy demo data over.")
def run_server(port: int, dev_mode: bool, no_open: bool, no_copy_demo_data: bool):
    _run_server(port, dev_mode, no_open, no_copy_demo_data)


@cli.command()
@click.option("--port", default=7241, help="Port to run the server on")
def demo_server(port: int):
    _run_server(port, True, False, False, "demos/chatbot")


@cli.command(help="Publishes the package to a repository")
@click.option("--prod", is_flag=True, help="Publish to pypi (rather than test pypi)")
@click.option("--no-wipe-dist", is_flag=True, help="Wipe the dist/ directory before building")
def build_and_publish(prod: bool, no_wipe_dist: bool):
    _telemetry_if_enabled("build_and_publish")
    git_root = _get_git_root()
    with cd(git_root):
        logger.info("Building UI -- this may take a bit...")
        _build_ui()
        logger.info("Built UI!")
        if not no_wipe_dist:
            logger.info("Wiping dist/ directory for a clean publish.")
            shutil.rmtree("dist", ignore_errors=True)
        _command("python3 -m build", capture_output=False)
        repository = "pypi" if prod else "testpypi"
        _command(f"python3 -m twine upload --repository {repository} dist/*", capture_output=False)
        logger.info(f"Published to {repository}! 🎉")


@cli.command(help="generate demo data for the UI")
def generate_demo_data():
    _telemetry_if_enabled("generate_demo_data")
    git_root = _get_git_root()
    # We need to add the examples directory to the path so we have all the imports
    # The GPT-one relies on a local import
    sys.path.extend([git_root, f"{git_root}/examples/multi-modal-chatbot"])
    from burr.cli.demo_data import generate_all

    with cd(git_root):
        logger.info("Removing old demo data")
        shutil.rmtree("burr/tracking/server/demo_data", ignore_errors=True)
        generate_all("burr/tracking/server/demo_data")


def _transform_state_to_test_case(state: dict, action_name: str, test_name: str) -> dict:
    """Helper function to transform a state into a test case.

    :param state:
    :param action_name:
    :param test_name:
    :return:
    """
    return {
        "action": action_name,
        "name": test_name,
        "input_state": state,
        "expected_state": {"TODO:": "fill this in"},
    }


@click.group()
def test_case():
    """Test case related commands."""
    pass


PYTEST_TEMPLATE = """import pytest
from burr.core import state
from burr.testing import pytest_generate_tests  # noqa: F401
# TODO: import action you're testing, i.e. import {ACTION_NAME}.

@pytest.mark.file_name("{FILE_NAME}")
def test_{ACTION_NAME}(input_state, expected_state):
    \"\"\"Function for testing the action\"\"\"
    input_state = state.State(input_state)
    expected_state = state.State(expected_state)
    _, output_state = {ACTION_NAME}(input_state)  # exercise the action
    # TODO: choose appropriate way to evaluate the output
    # e.g. exact match, fuzzy match, LLM grade, etc.
    # this is exact match here on all values in state
    assert output_state == expected_state
    # e.g.
    # assert 'some value' in output_state["response"]["content"]
    # assert llm_evaluator(..., ...) == "Y"
"""


@click.command()
@click.option("--project-name", required=True, help="Name of the project")
@click.option("--partition-key", required=True, help="Partition key to look at")
@click.option("--app-id", required=True, help="App ID to pull from.")
@click.option("--sequence-id", required=True, help="Sequence ID to pull.")
@click.option(
    "--target-file-name",
    required=False,
    help="What file to write the data to. Else print to console.",
)
def create_test_case(
    project_name: str,
    partition_key: str,
    app_id: str,
    sequence_id: str,
    target_file_name: str = None,
):
    """Create a test case from a persisted state.

    Does two things:

    1. Pulls data specified and saves it/prints to console.
    2. Prints a pytest test case to the console for you to cut and paste.

    See examples/test-case-creation/notebook.ipynb for example usage.
    See examples/test-case-creation/test_application.py for details.
    """
    # TODO: make this handle instantiating/using a persister other than local tracker
    from burr.tracking.client import LocalTrackingClient

    local_tracker = LocalTrackingClient(project=project_name)
    data: PersistedStateData = local_tracker.load(
        partition_key=partition_key, app_id=app_id, sequence_id=int(sequence_id)
    )
    if not data:
        print(f"No data found for {app_id} in {project_name} with sequence {sequence_id}")
        return
    state_dict = data["state"].get_all()
    print("Found data for action: ", data["position"])
    # test case json
    tc_json = _transform_state_to_test_case(
        state_dict, data["position"], f"{data['position']}_{app_id[:8] + '_' + str(sequence_id)}"
    )

    if target_file_name:
        # if it already exists, load it up and append to it
        if os.path.exists(target_file_name):
            with open(target_file_name, "r") as f:
                # assumes it's a list of test cases
                current_testcases = json.load(f)
            current_testcases.append(tc_json)
        else:
            current_testcases = [tc_json]
        print(f"\nWriting data to file {target_file_name}")
        with open(target_file_name, "w") as f:
            json.dump(current_testcases, f, indent=2)
    else:
        logger.info(json.dumps(tc_json, indent=2))
    # print out python test to add
    print("\nAdd the following to your test file:\n")
    print(PYTEST_TEMPLATE.format(FILE_NAME=target_file_name, ACTION_NAME=data["position"]))


test_case.add_command(create_test_case, name="create")
cli.add_command(test_case)

# quick trick to expose every subcommand as a variable
# will create a command called `cli_{command}` for every command we have
for key, command in cli.commands.items():
    globals()[f'cli_{key.replace("-", "_")}'] = command


if __name__ == "__main__":
    cli()
