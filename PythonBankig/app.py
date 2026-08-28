import sqlite3
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from flask import Flask, g, jsonify, request


app = Flask(__name__)

BASE_DIRECTORY = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIRECTORY / "finance.db"
ACCOUNT_ID = "ACC-1001"


def get_db():
    """Open one SQLite connection for the current request."""
    if "database" not in g:
        g.database = sqlite3.connect(DATABASE_PATH)
        g.database.row_factory = sqlite3.Row
        g.database.execute("PRAGMA foreign_keys = ON")

    return g.database


@app.teardown_appcontext
def close_db(error=None):
    """Close the request's database connection when Flask is finished."""
    database = g.pop("database", None)

    if database is not None:
        database.close()


def initialize_database():
    database = get_db()

    database.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            currency TEXT NOT NULL,
            balance_cents INTEGER NOT NULL DEFAULT 0
                CHECK (balance_cents >= 0)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL
                CHECK (transaction_type IN ('deposit', 'withdrawal')),
            amount_cents INTEGER NOT NULL
                CHECK (amount_cents > 0),
            balance_after_cents INTEGER NOT NULL
                CHECK (balance_after_cents >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        );
        """
    )

    database.execute(
        """
        INSERT OR IGNORE INTO accounts (
            id,
            owner,
            currency,
            balance_cents
        ) VALUES (?, ?, ?, ?)
        """,
        (ACCOUNT_ID, "Rainy Reaksmey", "USD", 100000),
    )
    database.commit()


def money_to_cents(value):
    """Convert a JSON money value such as 35.50 into 3550 cents."""
    try:
        amount = Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        if not amount.is_finite() or amount <= 0:
            return None

        return int(amount * 100)
    except (InvalidOperation, TypeError, ValueError):
        return None


def format_money(cents):
    return f"{Decimal(cents) / Decimal(100):.2f}"


def serialize_account(row):
    return {
        "id": row["id"],
        "owner": row["owner"],
        "currency": row["currency"],
        "balance": format_money(row["balance_cents"]),
    }


def serialize_transaction(row):
    return {
        "id": row["id"],
        "type": row["transaction_type"],
        "amount": format_money(row["amount_cents"]),
        "balance_after": format_money(row["balance_after_cents"]),
        "created_at": row["created_at"],
    }


@app.get("/")
def home():
    return jsonify(
        {
            "success": True,
            "message": "Financial API is running!",
            "endpoints": {
                "account": "GET /api/account",
                "deposit": "POST /api/deposit",
                "withdraw": "POST /api/withdraw",
                "transactions": "GET /api/transactions",
            },
        }
    )


@app.get("/api/account")
def get_account():
    account = get_db().execute(
        "SELECT * FROM accounts WHERE id = ?",
        (ACCOUNT_ID,),
    ).fetchone()

    return jsonify(
        {
            "success": True,
            "account": serialize_account(account),
        }
    )


@app.post("/api/deposit")
def deposit():
    data = request.get_json(silent=True) or {}
    amount_cents = money_to_cents(data.get("amount"))

    if amount_cents is None:
        return jsonify(
            {
                "success": False,
                "error": "Enter a valid amount greater than zero.",
            }
        ), 400

    database = get_db()

    try:
        database.execute("BEGIN IMMEDIATE")
        account = database.execute(
            "SELECT balance_cents FROM accounts WHERE id = ?",
            (ACCOUNT_ID,),
        ).fetchone()
        new_balance = account["balance_cents"] + amount_cents

        database.execute(
            "UPDATE accounts SET balance_cents = ? WHERE id = ?",
            (new_balance, ACCOUNT_ID),
        )
        cursor = database.execute(
            """
            INSERT INTO transactions (
                account_id,
                transaction_type,
                amount_cents,
                balance_after_cents
            ) VALUES (?, 'deposit', ?, ?)
            """,
            (ACCOUNT_ID, amount_cents, new_balance),
        )
        database.commit()
    except sqlite3.Error:
        database.rollback()
        return jsonify(
            {
                "success": False,
                "error": "The deposit could not be saved.",
            }
        ), 500

    transaction = database.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return jsonify(
        {
            "success": True,
            "message": "Deposit completed.",
            "transaction": serialize_transaction(transaction),
        }
    ), 201


@app.post("/api/withdraw")
def withdraw():
    data = request.get_json(silent=True) or {}
    amount_cents = money_to_cents(data.get("amount"))

    if amount_cents is None:
        return jsonify(
            {
                "success": False,
                "error": "Enter a valid amount greater than zero.",
            }
        ), 400

    database = get_db()

    try:
        database.execute("BEGIN IMMEDIATE")
        account = database.execute(
            "SELECT balance_cents FROM accounts WHERE id = ?",
            (ACCOUNT_ID,),
        ).fetchone()

        if amount_cents > account["balance_cents"]:
            database.rollback()
            return jsonify(
                {
                    "success": False,
                    "error": "Insufficient balance.",
                }
            ), 400

        new_balance = account["balance_cents"] - amount_cents

        database.execute(
            "UPDATE accounts SET balance_cents = ? WHERE id = ?",
            (new_balance, ACCOUNT_ID),
        )
        cursor = database.execute(
            """
            INSERT INTO transactions (
                account_id,
                transaction_type,
                amount_cents,
                balance_after_cents
            ) VALUES (?, 'withdrawal', ?, ?)
            """,
            (ACCOUNT_ID, amount_cents, new_balance),
        )
        database.commit()
    except sqlite3.Error:
        database.rollback()
        return jsonify(
            {
                "success": False,
                "error": "The withdrawal could not be saved.",
            }
        ), 500

    transaction = database.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()

    return jsonify(
        {
            "success": True,
            "message": "Withdrawal completed.",
            "transaction": serialize_transaction(transaction),
        }
    ), 201


@app.get("/api/transactions")
def get_transactions():
    rows = get_db().execute(
        """
        SELECT *
        FROM transactions
        WHERE account_id = ?
        ORDER BY id DESC
        """,
        (ACCOUNT_ID,),
    ).fetchall()

    return jsonify(
        {
            "success": True,
            "total": len(rows),
            "transactions": [serialize_transaction(row) for row in rows],
        }
    )


with app.app_context():
    initialize_database()


if __name__ == "__main__":
    app.run(debug=True)