import os

# hardcoded to work in current directory for now, but we can easily change
EXAMPLES_DIR = "."

# Required files for each example
REQUIRED_FILES = [
    "notebook.ipynb",
    "application.py",
    "README.md",
    "statemachine.png",
    "__init__.py",  # included as we want them all to be importable
]

FILTERLIST = ["other-examples", "ml-training", "simulation", "multi-agent-collaboration"]


def should_validate(directory: str) -> bool:
    """Return True if the given directory is an example directory."""
    return (
        os.path.isdir(os.path.join(EXAMPLES_DIR, directory))
        and not directory.startswith(".")
        and not directory.startswith("_")
        and directory not in FILTERLIST
    )


def get_directories(base_path: str) -> list[str]:
    """Return a list of directories under the given base_path."""
    return [d for d in os.listdir(base_path) if should_validate(d)]


def check_files_exist(directory, files):
    """Check if each file in 'files' exists in 'directory'."""
    missing_files = []
    for file in files:
        if not os.path.exists(os.path.join(EXAMPLES_DIR, directory, file)):
            missing_files.append(file)
    return missing_files


# Use pytest_generate_tests to dynamically parameterize the fixture
def pytest_generate_tests(metafunc):
    # if "directory" in metafunc.fixturenames:
    directories = get_directories(EXAMPLES_DIR)
    metafunc.parametrize("directory", directories, scope="module")


def test_directory_name(directory):
    if "_" in directory:
        assert (
            False
        ), f"Example Directory '{directory}' should not contain underscores, only dashes!."


def test_directory_contents(directory):
    missing_files = check_files_exist(directory, REQUIRED_FILES)
    assert (
        not missing_files
    ), f"Missing files in example dir '{directory}': {', '.join(missing_files)}"
