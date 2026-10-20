"""Unit tests for ProveedorModel CRUD operations and validation."""

import pytest
from src import models
from src.db.setup_db import init_db


@pytest.fixture
def temp_db(tmp_path):
    """Fixture that provides an initialized temporary database and resets Singleton."""
    db_path = str(tmp_path / "test_proveedor.db")
    init_db(db_path=db_path)
    models.ProveedorModel._instance = None
    return db_path


def test_proveedor_crud(temp_db) -> None:
    """Tests standard CRUD operations for ProveedorModel."""
    model = models.ProveedorModel(db_path=temp_db)

    assert model.create("900123456-1", "Proveedor Test", "Calle 10") is True

    assert len(model.get_all()) == 1
    prov = model.get_by_id("900123456-1")
    assert prov is not None
    assert prov["nombre"] == "Proveedor Test"
    assert prov["direccion"] == "Calle 10"

    assert model.update("900123456-1", "Nuevo Nombre Ltda.", "Calle 20") is True
    updated = model.get_by_id("900123456-1")
    assert updated["nombre"] == "Nuevo Nombre Ltda."
    assert updated["direccion"] == "Calle 20"

    assert model.delete("900123456-1") is True
    assert model.get_by_id("900123456-1") is None


def test_proveedor_edge_cases(temp_db) -> None:
    """Tests robust handling of duplicate primary keys and NOT NULL constraints."""
    model = models.ProveedorModel(db_path=temp_db)

    assert model.create("111", "Prov 1", "Dir 1") is True
    assert model.create("111", "Duplicado", "Dir 2") is False
    assert model.create("222", None, "Dir") is False  # type: ignore[arg-type]