"""Unit tests for ProductoModel CRUD operations and validation."""

import pytest
from src import models
from src.db.setup_db import init_db


@pytest.fixture
def temp_db(tmp_path):
    """Fixture that provides an initialized temporary database and resets Singletons."""
    db_path = str(tmp_path / "test_producto.db")
    init_db(db_path=db_path)
    models.ProveedorModel._instance = None
    models.ProductoModel._instance = None

    models.ProveedorModel(db_path=db_path).create(
        "NIT-01", "Proveedor Base", "Av. Principal"
    )
    return db_path


def test_producto_crud(temp_db) -> None:
    """Tests standard CRUD operations for ProductoModel."""
    model = models.ProductoModel(db_path=temp_db)

    assert model.create("PROD-1", "NIT-01", "Laptop", 3500000) is True

    assert len(model.get_all()) == 1
    prod = model.get_by_id("PROD-1")
    assert prod is not None
    assert prod["nombre"] == "Laptop"
    assert prod["precio_unitario"] == 3500000
    assert isinstance(prod["precio_unitario"], int)

    assert model.update("PROD-1", "NIT-01", "Laptop Pro", 3200000) is True
    updated = model.get_by_id("PROD-1")
    assert updated["nombre"] == "Laptop Pro"
    assert updated["precio_unitario"] == 3200000

    assert model.delete("PROD-1") is True
    assert model.get_by_id("PROD-1") is None


def test_producto_edge_cases(temp_db) -> None:
    """Tests foreign key violations and NOT NULL constraints for products."""
    model = models.ProductoModel(db_path=temp_db)
    
    assert model.create("PROD-2", "FAKE-NIT", "Mouse", 80000) is False
    assert model.create("PROD-3", "NIT-01", None, 50000) is False  # type: ignore[arg-type]