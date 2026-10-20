"""Order routes module for managing purchase order endpoints."""

import sqlite3
from datetime import date
from typing import Any

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from src import models

pedidos_bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


def _get_models() -> tuple[models.PedidoModel, models.ClienteModel, models.ProductoModel]:
    """Instantiates and returns order, client, and product repository models.

    Returns:
        Tuple[models.PedidoModel, models.ClienteModel, models.ProductoModel]:
            Initialized model instances.
    """
    db_path = current_app.config["DB_PATH"]
    return (
        models.PedidoModel(db_path=db_path),
        models.ClienteModel(db_path=db_path),
        models.ProductoModel(db_path=db_path),
    )


@pedidos_bp.route("")
def lista() -> str:
    """Renders the list view of all orders along with calculated totals.

    Returns:
        str: The rendered HTML template string.
    """
    pedidos_model, _, _ = _get_models()
    db_path = current_app.config["DB_PATH"]
    with sqlite3.connect(db_path) as conn:
        totals = dict(
            conn.execute(
                "SELECT id_pedido, SUM(cantidad * precio_compra) "
                "FROM Detalle_pedido GROUP BY id_pedido"
            ).fetchall()
        )
    return render_template(
        "pedidos/lista.html",
        pedidos=pedidos_model.get_all(),
        totales=totals,
    )


@pedidos_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo() -> Any:
    """Handles purchase order creation GET and POST operations.

    Returns:
        Any: The rendered HTML template string or a redirect response.
    """
    pedidos_model, clientes_model, productos_model = _get_models()
    client_list = clientes_model.get_all()
    product_list = productos_model.get_all()

    if not client_list or not product_list:
        flash(
            "Para hacer un pedido debe haber al menos un cliente y un producto.",
            "error",
        )
        return redirect(url_for("index"))

    selection = {
        "id_cliente": request.args.get("cliente", ""),
        "fecha": date.today().isoformat(),
    }
    quantities: dict[str, str] = {}

    if request.method == "POST":
        selection = {
            "id_cliente": request.form.get("id_cliente", ""),
            "fecha": request.form.get("fecha", "").strip(),
        }
        details: list[dict[str, Any]] = []
        validation_error = None

        for prod in product_list:
            raw_qty = request.form.get(f"cant_{prod['codigo']}", "").strip()
            quantities[prod["codigo"]] = raw_qty

            if raw_qty in ("", "0"):
                continue

            if not raw_qty.isdigit() or int(raw_qty) <= 0:
                validation_error = f"La cantidad para {prod['nombre']} debe ser un número entero mayor a cero."
                break

            precio_entero = round(float(prod["precio_unitario"]))

            details.append(
                {
                    "codigo_producto": prod["codigo"],
                    "cantidad": int(raw_qty),
                    "precio_compra": precio_entero,
                }
            )

        if not clientes_model.get_by_id(selection["id_cliente"]):
            validation_error = "Seleccione un cliente."
        elif not selection["fecha"]:
            validation_error = "Indique la fecha del pedido."
        elif validation_error is None and not details:
            validation_error = (
                "Agregue al menos un producto con cantidad mayor que cero."
            )

        if validation_error:
            flash(validation_error, "error")
        else:
            order_id = pedidos_model.create_pedido(
                selection["id_cliente"], selection["fecha"], details
            )
            if order_id:
                flash(f"Pedido #{order_id} registrado.", "ok")
                return redirect(url_for("clientes.lista"))
            flash("No se pudo registrar el pedido.", "error")

    return render_template(
        "pedidos/nuevo.html",
        clientes=client_list,
        productos=product_list,
        sel=selection,
        cantidades=quantities,
    )


@pedidos_bp.route("/<int:id_pedido>")
def detalle(id_pedido: int) -> str:
    """Renders detailed information for a specific purchase order.

    Args:
        id_pedido (int): Primary key identifier of the target order.

    Returns:
        str: The rendered HTML template string.
    """
    pedidos_model, clientes_model, productos_model = _get_models()
    order = pedidos_model.get_by_id(id_pedido) or abort(404)
    client = clientes_model.get_by_id(order["id_cliente"])
    product_names = {p["codigo"]: p["nombre"] for p in productos_model.get_all()}
    total_amount = sum(
        item["cantidad"] * item["precio_compra"] for item in order["detalles"]
    )
    return render_template(
        "pedidos/detalle.html",
        pedido=order,
        cliente=client,
        nombres=product_names,
        total=total_amount,
    )


@pedidos_bp.post("/<int:id_pedido>/eliminar")
def eliminar(id_pedido: int) -> Response:
    """Deletes a purchase order and its associated detail records.

    Args:
        id_pedido (int): Primary key identifier of the target order.

    Returns:
        Response: A HTTP redirect response to the order list view.
    """
    pedidos_model, _, _ = _get_models()
    if pedidos_model.delete(id_pedido):
        flash(f"Pedido #{id_pedido} eliminado.", "ok")
    else:
        flash("No se pudo eliminar el pedido.", "error")
    return redirect(url_for("pedidos.lista"))