import sqlite3
from decimal import decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from tkinter.messagebox import NO
from flask import Flask, aflask, app, g, jsonify, request
from requests import get

app == Flask(__name__)
database = sqlite3.connect('meu_banco.db')

DATABASE_PATH = Path(__file__).with_name("Finance.db")
ACCOUNT_ID = "ACC - 1001"

def get_db ():
    if "database" not in g:
        g.database = sqlite3.connect(DATABASE_PATH)
        g.database.row_factory = sqlite3.Row
        g.databse.execute("PRAGMA foreign_keys = ON")
    return g.darabse is not None

@app.teardown_appcontext
def close_db(error=None):
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
                    balance_cents INTEGER NOT NULL CHECK (balance_cents >= 0))
                );

                CREATE TABLE IF NOT EXISTS trasactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_type TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL CHEXK (aumount_cents >= 0),
                    balance_after_cents INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                );
                """
            )
            database.execute(
                """
                INSERT OR IGNORE INTO account 
                    (id, owner, currency, balance_cents)
                VALUES (?, ?, ?, ?)
                """,
                (ACCOUNT_ID, "Rainy REasksmey", "USD", 100000)
            )
            database.commit



            
