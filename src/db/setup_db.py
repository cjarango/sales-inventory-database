import logging
import os
import sqlite3

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def init_db(db_path: str | None = None) -> None:
    """Initializes the SQLite database schema in third normal form (3FN).

    Args:
        db_path (str | None, optional): Custom path for the SQLite database file.
            Defaults to None, placing it in the project root directory.

    Raises:
        sqlite3.Error: If a database error occurs during table creation.
    """
    if db_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, "../../"))
        db_path = os.path.join(root_dir, "database.db")

    if os.path.exists(db_path):
        logger.info(f"Database already exists at: {db_path}. Skipping creation.")
        return

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Proveedor (
                nit TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                direccion TEXT NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Cliente (
                identificacion TEXT PRIMARY KEY,
                nombres TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                direccion TEXT NOT NULL,
                fecha_nacimiento DATE NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Producto (
                codigo TEXT PRIMARY KEY,
                nit_proveedor TEXT NOT NULL,
                nombre TEXT NOT NULL,
                precio_unitario INTEGER NOT NULL,
                FOREIGN KEY (nit_proveedor) REFERENCES Proveedor (nit)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Pedido (
                id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente TEXT NOT NULL,
                fecha DATE NOT NULL,
                FOREIGN KEY (id_cliente) REFERENCES Cliente (identificacion)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Detalle_pedido (
                id_pedido INTEGER NOT NULL,
                codigo_producto TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_compra INTEGER NOT NULL,
                PRIMARY KEY (id_pedido, codigo_producto),
                FOREIGN KEY (id_pedido) REFERENCES Pedido (id_pedido)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (codigo_producto) REFERENCES Producto (codigo)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            );
        """)

        conn.commit()
        logger.info(f"Database and tables successfully created at: {db_path}")

    except sqlite3.Error as e:
        logger.error(f"SQLite error occurred while initializing database: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    init_db()