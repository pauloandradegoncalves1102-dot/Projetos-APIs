import tempfile
import unittest
from pathlib import Path

import app as financial_api


class FinancialApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        financial_api.DATABASE_PATH = Path(self.temp_directory.name) / "finance.db"

        with financial_api.app.app_context():
            financial_api.initialize_database()

        self.client = financial_api.app.test_client()

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_complete_financial_flow(self):
        account_response = self.client.get("/api/account")
        self.assertEqual(account_response.status_code, 200)
        self.assertEqual(account_response.get_json()["account"]["balance"], "1000.00")

        deposit_response = self.client.post(
            "/api/deposit",
            json={"amount": "250.00"},
        )
        self.assertEqual(deposit_response.status_code, 201)
        self.assertEqual(
            deposit_response.get_json()["transaction"]["balance_after"],
            "1250.00",
        )

        withdraw_response = self.client.post(
            "/api/withdraw",
            json={"amount": "33.50"},
        )
        self.assertEqual(withdraw_response.status_code, 201)
        self.assertEqual(
            withdraw_response.get_json()["transaction"]["balance_after"],
            "1216.50",
        )

        history_response = self.client.get("/api/transactions")
        history = history_response.get_json()
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(history["total"], 2)
        self.assertEqual(history["transactions"][0]["type"], "withdrawal")
        self.assertEqual(history["transactions"][1]["type"], "deposit")

    def test_invalid_amount_and_insufficient_balance(self):
        invalid_response = self.client.post("/api/deposit", json={"amount": 0})
        self.assertEqual(invalid_response.status_code, 400)

        insufficient_response = self.client.post(
            "/api/withdraw",
            json={"amount": "1000.01"},
        )
        self.assertEqual(insufficient_response.status_code, 400)
        self.assertEqual(
            insufficient_response.get_json()["error"],
            "Insufficient balance.",
        )


if __name__ == "__main__":
    unittest.main()