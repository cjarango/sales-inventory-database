"""Integration tests for Flask web endpoints and user workflows."""

import sqlite3

import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test_app.db"))
    app.config["TESTING"] = True
    return app.test_client()


def test_paginas_principales(client) -> None:
    for url in [
        "/",
        "/clientes",
        "/productos",
        "/proveedores",
        "/pedidos",
        "/pedidos/nuevo",
        "/consultas",
        "/pedidos/1",
    ]:
        assert client.get(url).status_code == 200, f"Failed GET request for {url}"

    for n in range(1, 5):
        assert client.get(f"/consultas/{n}").status_code == 200, f"Failed GET request for /consultas/{n}"


def test_crud_cliente(client) -> None:
    datos = {
        "identificacion": "999",
        "nombres": "Ana",
        "apellidos": "Ruiz",
        "direccion": "Calle 1",
        "fecha_nacimiento": "2000-05-05",
    }
    r = client.post("/clientes/nuevo", data=datos, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "Ana" in html and "Ruiz" in html

    r = client.post("/clientes/nuevo", data=datos, follow_redirects=True)
    assert "Ya existe un cliente" in r.get_data(as_text=True)

    datos["nombres"] = "Ana María"
    r = client.post("/clientes/999/editar", data=datos, follow_redirects=True)
    assert "Ana María" in r.get_data(as_text=True)

    r = client.post("/clientes/999/eliminar", follow_redirects=True)
    assert "Ana María" not in r.get_data(as_text=True)


def test_no_elimina_cliente_con_pedidos(client) -> None:
    r = client.post("/clientes/1040123456/eliminar", follow_redirects=True)
    assert "tiene 1 pedido" in r.get_data(as_text=True)


def test_crud_proveedor_y_producto(client) -> None:
    client.post(
        "/proveedores/nuevo",
        data={"nit": "1-1", "nombre": "Prov X", "direccion": "Cra 1"},
    )

    r = client.post(
        "/productos/nuevo",
        data={
            "codigo": "P-X",
            "nombre": "Mouse",
            "precio_unitario": "50000",
            "nit_proveedor": "1-1",
        },
        follow_redirects=True,
    )
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "Mouse" in html

    r = client.post("/proveedores/1-1/eliminar", follow_redirects=True)
    assert "suministra 1 producto" in r.get_data(as_text=True)

    r = client.post(
        "/productos/P-X/editar",
        data={
            "nombre": "Mouse inalámbrico",
            "precio_unitario": "abc",
            "nit_proveedor": "1-1",
        },
        follow_redirects=True,
    )
    assert "número entero mayor que cero" in r.get_data(as_text=True)

    r_prod = client.post("/productos/P-X/eliminar", follow_redirects=True)
    assert "Mouse" not in r_prod.get_data(as_text=True)

    r_prov = client.post("/proveedores/1-1/eliminar", follow_redirects=True)
    assert "Prov X" not in r_prov.get_data(as_text=True)


def test_realizar_pedido(client) -> None:
    db_path = client.application.config["DB_PATH"]
    
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT OR IGNORE INTO Proveedor (nit, nombre, direccion) VALUES ('NIT-TEST', 'Prov Test', 'Dir Test')")
        conn.execute("INSERT OR IGNORE INTO Cliente (identificacion, nombres, apellidos, direccion, fecha_nacimiento) VALUES ('CLI-TEST', 'ClienteTest', 'Prueba', 'Dir', '1995-01-01')")
        conn.execute("INSERT OR IGNORE INTO Producto (codigo, nit_proveedor, nombre, precio_unitario) VALUES ('PRD-TEST', 'NIT-TEST', 'ProdTest', 50000)")
        conn.commit()

    r = client.post(
        "/pedidos/nuevo",
        data={
            "id_cliente": "CLI-TEST",
            "fecha": "2026-10-18",
            "cant_PRD-TEST": "2",
        },
        follow_redirects=True,
    )
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "Clientes" in html or "Pedidos" in html

    r_empty = client.post(
        "/pedidos/nuevo",
        data={"id_cliente": "CLI-TEST", "fecha": "2026-10-18"},
        follow_redirects=True,
    )
    assert r_empty.status_code == 200
    assert "Nuevo pedido" in r_empty.get_data(as_text=True)

    html_consultas = client.get("/consultas/2").get_data(as_text=True)
    assert "ClienteTest" not in html_consultas