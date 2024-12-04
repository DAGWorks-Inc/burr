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
