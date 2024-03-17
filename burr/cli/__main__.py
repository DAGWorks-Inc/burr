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
    cmd = "ln -s telemetry/ui/build burr/tracking/server/build"
    _command(cmd, capture_output=False)


@cli.command()
def build_ui():
    git_root = _get_git_root()
    with cd(git_root):
        _build_ui()


@cli.command()
@click.option("--port", default=7241, help="Port to run the server on")
@click.option("--dev-mode", is_flag=True, help="Run the server in development mode")
@click.option("--no-open", is_flag=True, help="Run the server without opening it")
@click.option("--no-copy-demo_data", is_flag=True, help="Don't copy demo data over.")
def run_server(port: int, dev_mode: bool, no_open: bool, no_copy_demo_data: bool):
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
                "open_url": (open_url := f"http://localhost:{port}"),
                "check_url": f"{open_url}/ready",
            },
            daemon=True,
        )
        thread.start()
    _command(cmd, capture_output=False)


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
    sys.path.extend([git_root, f"{git_root}/examples/gpt"])
    from burr.cli.demo_data import generate_all

    with cd(git_root):
        logger.info("Removing old demo data")
        shutil.rmtree("burr/tracking/server/demo_data", ignore_errors=True)
        generate_all("burr/tracking/server/demo_data")


# quick trick to expose every subcommand as a variable
# will create a command called `cli_{command}` for every command we have
for key, command in cli.commands.items():
    globals()[f'cli_{key.replace("-", "_")}'] = command

if __name__ == "__main__":
    cli()
