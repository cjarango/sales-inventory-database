"""Product routes module for managing product inventory web endpoints."""

import sqlite3
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

productos_bp = Blueprint("productos", __name__, url_prefix="/productos")


def _get_models() -> tuple[models.ProductoModel, models.ProveedorModel]:
    """Instantiates and returns the product and supplier repository models.

    Returns:
        Tuple[models.ProductoModel, models.ProveedorModel]: Initialized model instances.
    """
    db_path = current_app.config["DB_PATH"]
    return models.ProductoModel(db_path=db_path), models.ProveedorModel(db_path=db_path)


def _count(sql: str, params: tuple[Any, ...] = ()) -> int:
    """Executes a scalar count SQL query against the active database.

    Args:
        sql (str): The SQL query string.
        params (Tuple[Any, ...], optional): Arguments to bind to the query. Defaults to ().

    Returns:
        int: The scalar integer result of the query.
    """
    with sqlite3.connect(current_app.config["DB_PATH"]) as conn:
        return conn.execute(sql, params).fetchone()[0]


def _extract_fields(form: Any, *names: str) -> list[str] | None:
    """Extracts and strips specified field values from an HTML form payload.

    Args:
        form (Any): The Flask request form object.
        *names (str): Variable number of field names to retrieve.

    Returns:
        Optional[List[str]]: A list of sanitized field values if all are non-empty;
            otherwise None.
    """
    values = [form.get(n, "").strip() for n in names]
    return None if any(v == "" for v in values) else values


def _parse_product_payload(form: Any, with_code: bool) -> list[Any] | None:
    """Validates and parses product payload attributes from form data.

    Args:
        form (Any): The Flask request form object.
        with_code (bool): Whether the product code field is expected in the payload.

    Returns:
        Optional[List[Any]]: The validated field values including integer price, or None.
    """
    names = (["codigo"] if with_code else []) + ["nit_proveedor", "nombre", "precio_unitario"]
    fields = _extract_fields(form, *names)
    if fields is None:
        flash("Todos los campos son obligatorios.", "error")
        return None
    try:
        unit_price = round(float(fields[-1]))
        if unit_price <= 0:
            raise ValueError
        fields[-1] = unit_price
    except ValueError:
        flash("El precio unitario debe ser un número entero mayor que cero.", "error")
        return None
    return fields


@productos_bp.route("")
def lista() -> str:
    """Renders the list view of all registered products.

    Returns:
        str: The rendered HTML template string.
    """
    prod_model, prov_model = _get_models()
    suppliers = {p["nit"]: p["nombre"] for p in prov_model.get_all()}
    return render_template(
        "productos/lista.html",
        productos=prod_model.get_all(),
        proveedores=suppliers,
    )


@productos_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo() -> Any:
    """Handles product creation GET and POST operations.

    Returns:
        Any: The rendered HTML template string or a redirect response.
    """
    prod_model, prov_model = _get_models()
    supplier_list = prov_model.get_all()
    if not supplier_list:
        flash("Primero registre al menos un proveedor.", "error")
        return redirect(url_for("proveedores.nuevo"))
    form_data = {}
    if request.method == "POST":
        form_data = request.form
        fields = _parse_product_payload(request.form, with_code=True)
        if fields is not None:
            if prod_model.get_by_id(fields[0]):
                flash(f"Ya existe un producto con código {fields[0]}.", "error")
            elif prod_model.create(*fields):
                flash(f"Producto {fields[2]} registrado.", "ok")
                return redirect(url_for("productos.lista"))
            else:
                flash("No se pudo registrar el producto.", "error")
    return render_template(
        "productos/form.html", p=form_data, proveedores=supplier_list, editar=False
    )


@productos_bp.route("/<codigo>/editar", methods=["GET", "POST"])
def editar(codigo: str) -> Any:
    """Handles product update GET and POST operations for a target product code.

    Args:
        codigo (str): The unique product alphanumeric code.

    Returns:
        Any: The rendered HTML template string or a redirect response.
    """
    prod_model, prov_model = _get_models()
    current_record = prod_model.get_by_id(codigo) or abort(404)
    if request.method == "POST":
        current_record = dict(request.form, codigo=codigo)
        fields = _parse_product_payload(request.form, with_code=False)
        if fields is not None:
            if prod_model.update(codigo, *fields):
                flash("Producto actualizado.", "ok")
                return redirect(url_for("productos.lista"))
            flash("No se pudo actualizar el producto.", "error")
    return render_template(
        "productos/form.html",
        p=current_record,
        proveedores=prov_model.get_all(),
        editar=True,
    )


@productos_bp.post("/<codigo>/eliminar")
def eliminar(codigo: str) -> Response:
    """Deletes a product record if it is not referenced in any order details.

    Args:
        codigo (str): The unique product alphanumeric code.

    Returns:
        Response: A HTTP redirect response to the product list view.
    """
    prod_model, _ = _get_models()
    referencing_orders = _count(
        "SELECT COUNT(*) FROM Detalle_pedido WHERE codigo_producto = ?", (codigo,)
    )
    if referencing_orders > 0:
        flash(
            f"No se puede eliminar: el producto aparece en {referencing_orders} pedido(s).",
            "error",
        )
    elif prod_model.delete(codigo):
        flash("Producto eliminado.", "ok")
    else:
        flash("No se pudo eliminar el producto.", "error")
    return redirect(url_for("productos.lista"))