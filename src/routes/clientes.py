"""Client routes module for managing client entity web endpoints."""

import sqlite3
from datetime import date, datetime
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

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


def _get_cliente_model() -> models.ClienteModel:
    """Instantiates and returns the ClienteModel configured with the current database path.

    Returns:
        models.ClienteModel: The initialized client repository model.
    """
    return models.ClienteModel(db_path=current_app.config["DB_PATH"])


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


def _es_fecha_valida(fecha_str: str) -> bool:
    """Valida que la fecha tenga formato correcto y no sea posterior a la fecha actual (Objetivo 1)."""
    try:
        fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        return fecha_dt <= date.today()
    except ValueError:
        return False


@clientes_bp.route("")
def lista() -> str:
    """Renders the list view of all registered clients.

    Returns:
        str: The rendered HTML template string.
    """
    model = _get_cliente_model()
    return render_template("clientes/lista.html", clientes=model.get_all())


@clientes_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo() -> Any:
    """Handles client creation GET and POST operations.

    Returns:
        Any: The rendered HTML template string or a redirect response.
    """
    model = _get_cliente_model()
    form_data = {}
    hoy = date.today().isoformat()

    if request.method == "POST":
        form_data = request.form
        fields = _extract_fields(
            request.form,
            "identificacion",
            "nombres",
            "apellidos",
            "direccion",
            "fecha_nacimiento",
        )
        if fields is None:
            flash("Todos los campos son obligatorios.", "error")
        elif not _es_fecha_valida(fields[4]):
            flash("La fecha de nacimiento no puede ser posterior a la fecha actual.", "error")
        elif model.get_by_id(fields[0]):
            flash(f"Ya existe un cliente con identificación {fields[0]}.", "error")
        elif model.create(*fields):
            flash(f"Cliente {fields[1]} {fields[2]} registrado.", "ok")
            return redirect(url_for("clientes.lista"))
        else:
            flash("No se pudo registrar el cliente.", "error")

    return render_template("clientes/form.html", c=form_data, editar=False, hoy=hoy)


@clientes_bp.route("/<identificacion>/editar", methods=["GET", "POST"])
def editar(identificacion: str) -> Any:
    """Handles client update GET and POST operations for a target identifier.

    Args:
        identificacion (str): The unique client identification number.

    Returns:
        Any: The rendered HTML template string or a redirect response.
    """
    model = _get_cliente_model()
    current_record = model.get_by_id(identificacion) or abort(404)
    hoy = date.today().isoformat()

    # Objetivo 4: Corregido 'dirección' por 'direccion'
    form_data = {
        "identificacion": current_record["identificacion"],
        "nombres": current_record["nombres"],
        "apellidos": current_record["apellidos"],
        "direccion": current_record["direccion"],
        "fecha_nacimiento": current_record["fecha_nacimiento"],
    }

    if request.method == "POST":
        form_data = dict(request.form, identificacion=identificacion)
        fields = _extract_fields(
            request.form, "nombres", "apellidos", "direccion", "fecha_nacimiento"
        )
        if fields is None:
            flash("Todos los campos son obligatorios.", "error")
        elif not _es_fecha_valida(fields[3]):
            flash("La fecha de nacimiento no puede ser posterior a la fecha actual.", "error")
        elif model.update(identificacion, *fields):
            flash("Cliente actualizado.", "ok")
            return redirect(url_for("clientes.lista"))
        else:
            flash("No se pudo actualizar el cliente.", "error")

    return render_template("clientes/form.html", c=form_data, editar=True, hoy=hoy)


@clientes_bp.post("/<identificacion>/eliminar")
def eliminar(identificacion: str) -> Response:
    """Deletes a client record if no associated orders exist.

    Args:
        identificacion (str): The unique client identification number.

    Returns:
        Response: A HTTP redirect response to the client list view.
    """
    model = _get_cliente_model()
    order_count = _count(
        "SELECT COUNT(*) FROM Pedido WHERE id_cliente = ?", (identificacion,)
    )
    if order_count > 0:
        flash(
            f"No se puede eliminar: el cliente tiene {order_count} pedido(s) registrado(s).",
            "error",
        )
    elif model.delete(identificacion):
        flash("Cliente eliminado.", "ok")
    else:
        flash("No se pudo eliminar el cliente.", "error")
    return redirect(url_for("clientes.lista"))