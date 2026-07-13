import tempfile
import unittest
from pathlib import Path

from signalops.storage import make_account_store


class StorageTests(unittest.TestCase):
    def test_empty_sqlite_store_starts_with_git_seed_accounts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = make_account_store(Path(tmp_dir) / "crm.sqlite")
            accounts = store.list_accounts()

            self.assertGreaterEqual(len(accounts), 10)
            self.assertIn("Factorial", {account["company_name"] for account in accounts})
            self.assertIn("Legora", {account["company_name"] for account in accounts})


if __name__ == "__main__":
    unittest.main()
