# Sistema de Ventas e Inventario — Laboratorio 01 (Bases de Datos)

Aplicación web en **Python + Flask** con base de datos **SQLite** que implementa el enunciado del Laboratorio 01.

## Cómo ejecutarla

**Forma fácil (Windows):** doble clic en `iniciar.bat`. Instala Flask la primera vez y abre el navegador solo. En Mac: doble clic en `iniciar.command`.

**Desde la terminal:**

```bash
pip install -r requirements.txt
python app.py
```

El navegador se abre solo en <http://127.0.0.1:5000>.

Si `database.db` no existe, la app la crea (`src/db/setup_db.py`) y la llena con datos de prueba (`src/db/seed_db.py`).
Para empezar con datos limpios, borre `database.db` y vuelva a ejecutar.

## Menú

| Opción | Ruta | Qué hace |
|---|---|---|
| 1. Clientes | `/clientes` | Insertar, actualizar y borrar clientes |
| 2. Productos | `/productos` | Insertar, actualizar y borrar productos (cada uno con su proveedor) |
| 3. Proveedores | `/proveedores` | Insertar, actualizar y borrar proveedores |
| 4. Pedidos | `/pedidos` | Un cliente realiza pedidos de uno o varios productos |
| 5. Consultas | `/consultas` | Las 4 consultas del enunciado |

Reglas de integridad: no se puede borrar un cliente con pedidos, un producto que esté en un pedido ni un proveedor que suministre productos (`ON DELETE RESTRICT`). Al borrar un pedido se borran sus detalles (`ON DELETE CASCADE`).

## Estructura

```
app.py                  # Aplicación Flask (rutas del menú)
src/db/setup_db.py      # Script de creación de tablas
src/db/seed_db.py       # Datos de prueba
src/models/             # Acceso a datos (CRUD y consultas SQL)
src/templates/          # Vistas HTML (Jinja2)
diagrams/               # Diagrama E-R y modelo relacional (draw.io)
tests/unit/             # Pruebas (pytest)
```

## Pruebas

```bash
python -m pytest tests
```
