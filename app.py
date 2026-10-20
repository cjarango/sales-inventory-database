import os
import sqlite3
import sys
import threading
import webbrowser
from typing import Any

from flask import Flask, render_template
from src.db.seed_db import seed_database
from src.db.setup_db import init_db
from src.routes import (
    clientes_bp,
    consultas_bp,
    pedidos_bp,
    productos_bp,
    proveedores_bp,
)

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_DB = os.path.join(BASE_DIR, "database.db")


def create_app(db_path: str = DEFAULT_DB, seed: bool = True) -> Flask:
    if getattr(sys, 'frozen', False):
        template_dir = os.path.join(sys._MEIPASS, "src", "templates")
    else:
        template_dir = os.path.join(BASE_DIR, "src", "templates")

    app = Flask(__name__, template_folder=template_dir)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "laboratorio-01-bd")
    app.config["DB_PATH"] = db_path

    init_db(db_path=db_path)
    if seed:
        seed_database(db_path=db_path)

    app.register_blueprint(clientes_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(proveedores_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(consultas_bp)

    @app.route("/")
    def index() -> str:
        def scalar_count(sql: str) -> int:
            with sqlite3.connect(db_path) as conn:
                return conn.execute(sql).fetchone()[0]

        counts = {
            "clientes": scalar_count("SELECT COUNT(*) FROM Cliente"),
            "productos": scalar_count("SELECT COUNT(*) FROM Producto"),
            "proveedores": scalar_count("SELECT COUNT(*) FROM Proveedor"),
            "pedidos": scalar_count("SELECT COUNT(*) FROM Pedido"),
        }
        return render_template("index.html", totales=counts)

    @app.template_filter("pesos")
    def currency_format(value: Any) -> str:
        if value is None:
            return "—"
        return "$ " + f"{value:,.0f}".replace(",", ".")

    @app.errorhandler(404)
    def page_not_found(_: Exception) -> Any:
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()

    create_app().run(debug=False)