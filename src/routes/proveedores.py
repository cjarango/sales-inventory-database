"""Supplier routes module for managing supplier entity web endpoints."""

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

proveedores_bp = Blueprint("proveedores", __name__, url_prefix="/proveedores")


def _get_proveedor_model() -> models.ProveedorModel:
    """Instantiates and returns the ProveedorModel configured with the active database path.

    Returns:
        models.ProveedorModel: The initialized supplier repository model.
    """
    return models.ProveedorModel(db_path=current_app.config["DB_PATH"])


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


@proveedores_bp.route("")
def lista() -> str:
    """Renders the list view of all registered suppliers.

    Returns:
        str: The rendered HTML template string.
    """
    model = _get_proveedor_model()
    return render_template("proveedores/lista.html", proveedores=model.get_all())


@proveedores_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo() -> Any:
    """Handles supplier creation GET and POST operations.

    Returns:
        Any: The rendered HTML template string or a redirect response.
    """
    model = _get_proveedor_model()
    form_data = {}
    if request.method == "POST":
        form_data = request.form
        fields = _extract_fields(request.form, "nit", "nombre", "direccion")
        if fields is None:
            flash("Todos los campos son obligatorios.", "error")
        elif model.get_by_id(fields[0]):
            flash(f"Ya existe un proveedor con NIT {fields[0]}.", "error")
        elif model.create(*fields):
            flash(f"Proveedor {fields[1]} registrado.", "ok")
            return redirect(url_for("proveedores.lista"))
        else:
            flash("No se pudo registrar el proveedor.", "error")
    return render_template("proveedores/form.html", p=form_data, editar=False)


@proveedores_bp.route("/<nit>/editar", methods=["GET", "POST"])
def editar(nit: str) -> Any:
    """Handles supplier update GET and POST operations for a target NIT.

    Args:
        nit (str): The supplier unique tax identifier (NIT).

    Returns:
        Any: The rendered HTML template string or a redirect response.
    """
    model = _get_proveedor_model()
    current_record = model.get_by_id(nit) or abort(404)
    if request.method == "POST":
        current_record = dict(request.form, nit=nit)
        fields = _extract_fields(request.form, "nombre", "direccion")
        if fields is None:
            flash("Todos los campos son obligatorios.", "error")
        elif model.update(nit, *fields):
            flash("Proveedor actualizado.", "ok")
            return redirect(url_for("proveedores.lista"))
        else:
            flash("No se pudo actualizar el proveedor.", "error")
    return render_template("proveedores/form.html", p=current_record, editar=True)


@proveedores_bp.post("/<nit>/eliminar")
def eliminar(nit: str) -> Response:
    """Deletes a supplier record if it has no associated products.

    Args:
        nit (str): The supplier unique tax identifier (NIT).

    Returns:
        Response: A HTTP redirect response to the supplier list view.
    """
    model = _get_proveedor_model()
    product_count = _count(
        "SELECT COUNT(*) FROM Producto WHERE nit_proveedor = ?", (nit,)
    )
    if product_count > 0:
        flash(
            f"No se puede eliminar: el proveedor suministra {product_count} producto(s).",
            "error",
        )
    elif model.delete(nit):
        flash("Proveedor eliminado.", "ok")
    else:
        flash("No se pudo eliminar el proveedor.", "error")
    return redirect(url_for("proveedores.lista"))