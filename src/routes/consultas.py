"""Analytics routes module for handling relational report queries."""

from flask import Blueprint, abort, current_app, render_template
from src import models

consultas_bp = Blueprint("consultas", __name__, url_prefix="/consultas")


def _get_reporte_model() -> models.ReporteModel:
    """Instantiates and returns the ReporteModel for query execution.

    Returns:
        models.ReporteModel: The initialized analytical report model.
    """
    return models.ReporteModel(db_path=current_app.config["DB_PATH"])


@consultas_bp.route("")
def index() -> str:
    """Renders the main analytics and reports menu page.

    Returns:
        str: The rendered HTML template string.
    """
    reports_map: dict[int, str] = {
        1: "Clientes y cantidad de pedidos realizados",
        2: "Clientes que no realizaron ningún pedido",
        3: "Productos comprados por cliente y proveedor",
        4: "Proveedores con los productos suministrados",
    }
    return render_template("consultas/index.html", consultas=reports_map)


@consultas_bp.route("/<int:numero>")
def ver(numero: int) -> str:
    """Executes and renders the specified analytical query output.

    Args:
        numero (int): The numerical identifier of the query (1 to 4).

    Returns:
        str: The rendered HTML template string displaying query results.

    Raises:
        HTTPException: 404 error if the requested query index is invalid.
    """
    reports_model = _get_reporte_model()
    queries = {
        1: (
            "Clientes y cantidad de pedidos realizados",
            reports_model.clientes_con_conteo_pedidos,
            [
                ("identificacion", "Identificación"),
                ("nombres", "Nombres"),
                ("apellidos", "Apellidos"),
                ("total_pedidos", "Total pedidos"),
            ],
        ),
        2: (
            "Clientes que no realizaron ningún pedido",
            reports_model.clientes_sin_pedidos,
            [
                ("identificacion", "Identificación"),
                ("nombres", "Nombres"),
                ("apellidos", "Apellidos"),
                ("direccion", "Dirección"),
                ("fecha_nacimiento", "Fecha de nacimiento"),
            ],
        ),
        3: (
            "Productos comprados por cliente y proveedor",
            reports_model.detalle_completo_compras,
            [
                ("nombre_cliente", "Cliente"),
                ("nombre_producto", "Producto"),
                ("cantidad", "Cantidad"),
                ("precio_compra", "Precio de compra"),
                ("nombre_proveedor", "Proveedor"),
            ],
        ),
        4: (
            "Proveedores con los productos suministrados",
            reports_model.proveedores_con_productos,
            [
                ("nit", "NIT"),
                ("nombre_proveedor", "Proveedor"),
                ("direccion", "Dirección"),
                ("codigo_producto", "Código producto"),
                ("nombre_producto", "Producto"),
                ("precio_unitario", "Precio unitario"),
            ],
        ),
    }

    if numero not in queries:
        abort(404)

    title, query_func, columns = queries[numero]
    return render_template(
        "consultas/resultado.html",
        numero=numero,
        titulo=title,
        columnas=columns,
        filas=query_func(),
    )