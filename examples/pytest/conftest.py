import subprocess

import pytest


class ResultCollector:
    """Example of a custom fixture that collects results from tests."""

    def __init__(self):
        self.results = []

    def append(self, result):
        self.results.append(result)

    def values(self):
        return self.results

    def __str__(self):
        return "\n".join(str(result) for result in self.results)


@pytest.fixture(scope="session")
def result_collector():
    """Fixture that collects results from tests. This is a toy example."""
    collector = ResultCollector()
    yield collector
    print("\nCollected Results:\n", collector)


@pytest.fixture
def git_info():
    """Fixture that returns the git commit, branch, latest_tag.

    Note if there are uncommitted changes, the commit will have '-dirty' appended.
    """
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode("utf-8")
        dirty = subprocess.check_output(["git", "status", "--porcelain"]).strip() != b""
        commit = f"{commit}{'-dirty' if dirty else ''}"
    except subprocess.CalledProcessError:
        commit = None
    try:
        latest_tag = (
            subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"])
            .strip()
            .decode("utf-8")
        )
    except subprocess.CalledProcessError:
        latest_tag = None
    try:
        branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .strip()
            .decode("utf-8")
        )
    except subprocess.CalledProcessError:
        branch = None
    return {"commit": commit, "latest_tag": latest_tag, "branch": branch}


def pytest_configure(config):
    """Code to stop custom mark warnings"""
    config.addinivalue_line(
        "markers", "file_name: mark test to run using Burr file-based parameterization."
    )
