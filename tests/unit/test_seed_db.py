"""Unit tests for database seeding module with test data."""

import sqlite3

import pytest
from src.db.seed_db import seed_database
from src.db.setup_db import init_db


def test_seed_database_not_found(tmp_path) -> None:
    """Verifies that FileNotFoundError is raised when the database file is missing."""
    db_path = str(tmp_path / "non_existent.db")

    with pytest.raises(FileNotFoundError):
        seed_database(db_path=db_path)


def test_seed_database_when_empty(tmp_path) -> None:
    """Verifies that seed data is populated when the database exists but contains no records."""
    db_path = str(tmp_path / "empty.db")
    init_db(db_path=db_path)

    seed_database(db_path=db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Cliente;")
    client_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Producto;")
    prod_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Proveedor;")
    prov_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Pedido;")
    pedido_count = cursor.fetchone()[0]

    conn.close()

    assert client_count > 0
    assert prod_count > 0
    assert prov_count > 0
    assert pedido_count > 0


def test_seed_database_when_populated(tmp_path) -> None:
    """Verifies that seeding is skipped if the database already contains records."""
    db_path = str(tmp_path / "populated.db")
    init_db(db_path=db_path)
    seed_database(db_path=db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Cliente;")
    initial_count = cursor.fetchone()[0]
    conn.close()

    seed_database(db_path=db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Cliente;")
    final_count = cursor.fetchone()[0]
    conn.close()

    assert final_count == initial_count