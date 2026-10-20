"""Unit tests for ClienteModel CRUD operations and edge cases."""

import pytest
from src import models
from src.db.setup_db import init_db


@pytest.fixture
def temp_db(tmp_path):
    """Fixture that provides an initialized temporary database and resets Singleton."""
    db_path = str(tmp_path / "test_cliente.db")
    init_db(db_path=db_path)
    models.ClienteModel._instance = None
    return db_path


def test_cliente_crud(temp_db) -> None:
    """Tests standard CRUD operations for ClienteModel."""
    model = models.ClienteModel(db_path=temp_db)

    assert (
        model.create(
            "12345", "Juan", "Mendoza", "Carrera 50", "2000-01-01"
        )
        is True
    )

    assert len(model.get_all()) == 1
    client = model.get_by_id("12345")
    assert client is not None
    assert client["nombres"] == "Juan"
    assert client["direccion"] == "Carrera 50"

    assert (
        model.update("12345", "Juan", "Pérez", "Carrera 50", "2000-01-01")
        is True
    )
    updated = model.get_by_id("12345")
    assert updated["apellidos"] == "Pérez"

    assert model.delete("12345") is True
    assert model.get_by_id("12345") is None


def test_cliente_edge_cases(temp_db) -> None:
    """Tests robust handling of missing mandatory fields."""
    model = models.ClienteModel(db_path=temp_db)
    
    assert (
        model.create(
            "999", "Carlos", None, "Calle Falsa", "1990-01-01"
        )
        is False  # type: ignore[arg-type]
    )