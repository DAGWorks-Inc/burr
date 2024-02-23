import os
import shutil
import subprocess
import threading
import time
import webbrowser
from contextlib import contextmanager

import click
import requests
from loguru import logger


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
def run_server(port: int, dev_mode: bool, no_open: bool):
    # TODO: Implement server running logic here
    # Example: Start a web server, configure ports, etc.
    logger.info(f"Starting server on port {port}")
    cmd = f"uvicorn burr.tracking.server.run:app --port {port}"
    if dev_mode:
        cmd += " --reload"
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


# quick trick to expose every subcommand as a variable
# will create a command called `cli_{command}` for every command we have
for key, command in cli.commands.items():
    globals()[f'cli_{key.replace("-", "_")}'] = command

if __name__ == "__main__":
    cli()
