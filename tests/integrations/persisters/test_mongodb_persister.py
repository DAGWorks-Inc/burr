import unittest

from burr.core import state
from burr.integrations.persisters.b_mongodb import MongoDBPersister


class TestMongoDBPersister(unittest.TestCase):
    def setUp(self):
        self.persister = MongoDBPersister(
            uri="mongodb://localhost:27017", db_name="testdb", collection_name="testcollection"
        )

    def tearDown(self):
        self.persister.collection.drop()

    def test_save_and_load_state(self):
        self.persister.save("pk", "app_id", 1, "pos", state.State({"a": 1, "b": 2}), "completed")
        data = self.persister.load("pk", "app_id", 1)
        self.assertEqual(data["state"].get_all(), {"a": 1, "b": 2})

    def test_list_app_ids(self):
        self.persister.save("pk", "app_id1", 1, "pos1", state.State({"a": 1}), "completed")
        self.persister.save("pk", "app_id2", 2, "pos2", state.State({"b": 2}), "completed")
        app_ids = self.persister.list_app_ids("pk")
        self.assertIn("app_id1", app_ids)
        self.assertIn("app_id2", app_ids)

    def test_load_nonexistent_key(self):
        state_data = self.persister.load("pk", "nonexistent_key")
        self.assertIsNone(state_data)


if __name__ == "__main__":
    unittest.main()
