"""Unit tests for database initialization and schema setup module."""

import os
import sqlite3

import pytest
from src.db.setup_db import init_db


def test_init_db_creates_tables(tmp_path) -> None:
    """Tests that init_db creates all required normalized tables successfully."""
    test_db_path = str(tmp_path / "test_database.db")

    init_db(db_path=test_db_path)

    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "Proveedor",
        "Cliente",
        "Producto",
        "Pedido",
        "Detalle_pedido",
    }

    assert expected_tables.issubset(
        tables
    ), f"Missing tables in schema. Found: {tables}"

    cursor.execute("PRAGMA table_info(Cliente);")
    columns = {row[1] for row in cursor.fetchall()}
    assert "direccion" in columns, "Column 'direccion' not found in Cliente schema."
    assert "dirección" not in columns, "Deprecated column 'dirección' found in Cliente schema."

    conn.close()


def test_init_db_skips_if_already_exists(tmp_path) -> None:
    """Tests that init_db safely skips creation if the database file already exists."""
    test_db_path = str(tmp_path / "test_database.db")

    init_db(db_path=test_db_path)
    assert os.path.exists(test_db_path)

    init_db(db_path=test_db_path)
    assert os.path.exists(test_db_path)