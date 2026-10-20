"""Unit tests for ReporteModel analytics and report queries."""

import pytest
from src import models
from src.db.setup_db import init_db


@pytest.fixture
def temp_db(tmp_path):
    """Provides a temporary test database populated with fixtures."""
    db_path = str(tmp_path / "test_reportes.db")
    init_db(db_path=db_path)

    models.ProveedorModel._instance = None
    models.ClienteModel._instance = None
    models.ProductoModel._instance = None
    models.PedidoModel._instance = None
    models.ReporteModel._instance = None

    prov_model = models.ProveedorModel(db_path=db_path)
    client_model = models.ClienteModel(db_path=db_path)
    prod_model = models.ProductoModel(db_path=db_path)
    pedido_model = models.PedidoModel(db_path=db_path)

    prov_model.create("NIT-1", "Tech Solutions", "Calle 100")
    prov_model.create("NIT-2", "Office Depot", "Av. Circunvalar")

    client_model.create("CLI-1", "Carlos", "Pérez", "Calle 50", "1990-01-01")
    client_model.create("CLI-2", "María", "Gómez", "Carrera 40", "1995-05-15")
    client_model.create("CLI-3", "Luisa", "Martínez", "Calle 80", "2000-10-20")

    prod_model.create("PROD-1", "NIT-1", 'Monitor 24"', 850000)
    prod_model.create("PROD-2", "NIT-1", "Teclado Mecánico", 250000)
    prod_model.create("PROD-3", "NIT-2", "Silla Ergonómica", 1200000)

    detalles_p1 = [
        {"codigo_producto": "PROD-1", "cantidad": 1, "precio_compra": 850000},
        {"codigo_producto": "PROD-2", "cantidad": 2, "precio_compra": 250000},
    ]
    pedido_model.create_pedido("CLI-1", "2026-10-01", detalles_p1)

    detalles_p2 = [
        {"codigo_producto": "PROD-3", "cantidad": 1, "precio_compra": 1200000}
    ]
    pedido_model.create_pedido("CLI-2", "2026-10-05", detalles_p2)

    return db_path


def test_consulta_clientes_con_conteo_pedidos(temp_db) -> None:
    reporte = models.ReporteModel(db_path=temp_db)
    resultados = reporte.clientes_con_conteo_pedidos()

    assert len(resultados) == 3

    data = {row["identificacion"]: row["total_pedidos"] for row in resultados}

    assert data["CLI-1"] == 1
    assert data["CLI-2"] == 1
    assert data["CLI-3"] == 0


def test_consulta_clientes_sin_pedidos(temp_db) -> None:
    reporte = models.ReporteModel(db_path=temp_db)
    resultados = reporte.clientes_sin_pedidos()

    assert len(resultados) == 1
    assert resultados[0]["identificacion"] == "CLI-3"
    assert resultados[0]["nombres"] == "Luisa"
    assert "direccion" in resultados[0]
    assert resultados[0]["direccion"] == "Calle 80"


def test_consulta_detalle_completo_compras(temp_db) -> None:
    reporte = models.ReporteModel(db_path=temp_db)
    resultados = reporte.detalle_completo_compras()

    assert len(resultados) == 3

    primer_item = resultados[0]
    assert "nombre_cliente" in primer_item
    assert "nombre_producto" in primer_item
    assert "cantidad" in primer_item
    assert "precio_compra" in primer_item
    assert "nombre_proveedor" in primer_item

    silla_compra = next(
        r for r in resultados if r["nombre_producto"] == "Silla Ergonómica"
    )
    assert silla_compra["nombre_cliente"] == "María Gómez"
    assert silla_compra["nombre_proveedor"] == "Office Depot"
    assert silla_compra["precio_compra"] == 1200000
    assert isinstance(silla_compra["precio_compra"], int)


def test_consulta_proveedores_con_productos(temp_db) -> None:
    reporte = models.ReporteModel(db_path=temp_db)
    resultados = reporte.proveedores_con_productos()

    assert len(resultados) == 3

    tech_products = [
        r["nombre_producto"]
        for r in resultados
        if r["nombre_proveedor"] == "Tech Solutions"
    ]
    assert 'Monitor 24"' in tech_products
    assert "Teclado Mecánico" in tech_products