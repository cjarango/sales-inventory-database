"""Unit tests for PedidoModel creation, retrieval, and deletion operations."""

import pytest
from src import models
from src.db.setup_db import init_db


@pytest.fixture
def temp_db(tmp_path):
    """Fixture that provides an initialized temporary database and resets Singletons."""
    db_path = str(tmp_path / "test_pedido.db")
    init_db(db_path=db_path)
    models.ProveedorModel._instance = None
    models.ClienteModel._instance = None
    models.ProductoModel._instance = None
    models.PedidoModel._instance = None

    models.ProveedorModel(db_path=db_path).create("NIT-1", "Prov", "Dir")
    models.ClienteModel(db_path=db_path).create(
        "CLI-1", "Ana", "García", "Calle 1", "1995-05-05"
    )
    models.ProductoModel(db_path=db_path).create("PRD-1", "NIT-1", "Teclado", 120000)

    return db_path


def test_pedido_crud(temp_db) -> None:
    """Tests order creation with details, retrieval, and deletion."""
    model = models.PedidoModel(db_path=temp_db)
    detalles = [{"codigo_producto": "PRD-1", "cantidad": 3, "precio_compra": 120000}]

    pedido_id = model.create_pedido("CLI-1", "2026-10-18", detalles)
    assert pedido_id is not None
    assert len(model.get_all()) == 1

    order = model.get_by_id(pedido_id)
    assert order is not None
    assert order["id_cliente"] == "CLI-1"
    assert len(order["detalles"]) == 1
    assert order["detalles"][0]["cantidad"] == 3
    assert order["detalles"][0]["precio_compra"] == 120000
    assert isinstance(order["detalles"][0]["precio_compra"], int)

    assert model.delete(pedido_id) is True
    assert model.get_by_id(pedido_id) is None


def test_pedido_edge_cases(temp_db) -> None:
    """Tests edge cases like empty details or non-existent client."""
    model = models.PedidoModel(db_path=temp_db)

    assert model.create_pedido("CLI-1", "2026-10-18", []) is None

    detalles = [{"codigo_producto": "PRD-1", "cantidad": 1, "precio_compra": 120000}]
    assert model.create_pedido("FAKE-CLI", "2026-10-18", detalles) is None