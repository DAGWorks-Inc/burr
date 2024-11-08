import enum
import os
import subprocess

from IPython.core.magic import Magics, line_magic, magics_class
from IPython.core.shellapp import InteractiveShellApp


class NotebookEnvironment(enum.Enum):
    JUPYTER = enum.auto()
    COLAB = enum.auto()
    VSCODE = enum.auto()
    DATABRICKS = enum.auto()
    KAGGLE = enum.auto()


def identify_notebook_environment(ipython: InteractiveShellApp) -> NotebookEnvironment:
    if "IPKernelApp" in ipython.config:
        return NotebookEnvironment.JUPYTER

    if os.environ.get("VSCODE_PID"):
        return NotebookEnvironment.VSCODE

    try:
        import google.colab  # noqa: F401

        return NotebookEnvironment.COLAB
    except ModuleNotFoundError:
        pass

    # TODO add Databricks implementation
    try:
        import dbruntime  # noqa: F401

        return NotebookEnvironment.DATABRICKS
    except ModuleNotFoundError:
        pass

    # TODO add Kaggle implementation
    try:
        import kaggle  # noqa: F401

        return NotebookEnvironment.KAGGLE
    except ModuleNotFoundError:
        pass

    raise RuntimeError(
        f"Unknown notebook environment. Known environments: {list(NotebookEnvironment)}"
    )


def launch_ui_colab():
    """Opens a Google Colab port and launches the Burr UI in a subprocess.

    Using a subprocess ensures that the Burr server logs aren't displayed in
    Colab cell outputs.

    NOTE. This will not work in a Jupyter notebook
    """
    from google.colab.output import eval_js

    PORT = 7241
    burr_ui_url = eval_js(f"google.colab.kernel.proxyPort({PORT})")
    process = subprocess.Popen(
        [
            "python",
            "-c",
            f"import uvicorn; from burr.tracking.server.run import app; uvicorn.run(app, host='127.0.0.1', port={PORT})",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process, burr_ui_url


def launch_ui_jupyter():
    """Launch the Burr UI in a subprocess.

    Using a subprocess ensures that the Burr server logs aren't displayed in Colab cell outputs
    """
    HOST = "127.0.0.1"
    PORT = 7241
    process = subprocess.Popen(
        [
            "python",
            "-c",
            f"import uvicorn; from burr.tracking.server.run import app; uvicorn.run(app, host='{HOST}', port={PORT})",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process, f"http://{HOST}:{PORT}"


def launch_ui(notebook_env: NotebookEnvironment) -> tuple:
    process, url = None, None
    if notebook_env == NotebookEnvironment.COLAB:
        process, url = launch_ui_colab()
    else:
        try:
            process, url = launch_ui_jupyter()
        except ModuleNotFoundError as e:
            raise RuntimeError(
                f"Failed to launch Burr UI for environment {notebook_env}. Please report this issue."
            ) from e

    return process, url


@magics_class
class NotebookMagics(Magics):
    def __init__(self, notebook_env: NotebookEnvironment, **kwargs):
        super().__init__(**kwargs)
        self.notebook_env = notebook_env
        self.process = None
        self.url = None

    @line_magic
    def burr_ui(self, line):
        """Launch the Burr UI from a notebook cell"""
        if self.process is not None:
            print(f"Burr UI already running at {self.url}")
            return

        self.process, self.url = launch_ui(self.notebook_env)
        print(f"Burr UI: {self.url}")


def load_ipython_extension(ipython: InteractiveShellApp):
    """
    Any module file that define a function named `load_ipython_extension`
    can be loaded via `%load_ext module.path` or be configured to be
    autoloaded by IPython at startup time.
    """
    ipython.register_magics(NotebookMagics(notebook_env=identify_notebook_environment(ipython)))
