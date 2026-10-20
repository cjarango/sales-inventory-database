import logging
import os
import sqlite3

from src import models

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def seed_database(db_path: str = "database.db") -> None:
    """Verifies that the SQLite database exists; raises an error if it does not.

    If the database exists, checks if it is already populated. If it contains
    records, it leaves it untouched. If it is empty, it populates it with initial seed
    data.

    Args:
        db_path (str): The target file path for the SQLite database.

    Raises:
        FileNotFoundError: If the database file does not exist.
    """
    if not os.path.exists(db_path):
        error_msg = (
            f"Database not found at '{db_path}'. Please use setup_db.py or create"
            " the database first."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    is_populated = False
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='Cliente';"
        )
        table_exists = cursor.fetchone()

        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM Cliente;")
            count = cursor.fetchone()[0]
            if count > 0:
                is_populated = True

        conn.close()
    except sqlite3.Error as e:
        logger.warning(
            f"Could not verify existing database contents due to error: {e}"
        )

    if is_populated:
        logger.info(
            f"Database exists at '{db_path}' and is already populated. Skipping"
            " seeding."
        )
        return

    logger.info(
        f"Database exists at '{db_path}' but is empty. Proceeding with initial"
        " seeding."
    )

    models.ProveedorModel._instance = None
    models.ClienteModel._instance = None
    models.ProductoModel._instance = None
    models.PedidoModel._instance = None

    prov_model = models.ProveedorModel(db_path=db_path)
    client_model = models.ClienteModel(db_path=db_path)
    prod_model = models.ProductoModel(db_path=db_path)
    pedido_model = models.PedidoModel(db_path=db_path)

    logger.info("Populating database with initial seed records.")

    try:
        prov_model.create(
            "900123456-1", "Tech Solutions S.A.S.", "Calle 79 # 53-12"
        )
        prov_model.create(
            "800987654-2", "Suministros del Norte Ltda.", "Carrera 46 # 84-20"
        )
        prov_model.create("901112233-3", "Distribuidora Caribe", "Calle 30 # 20-05")

        client_model.create(
            "1040123456", "Carlos", "Pérez", "Calle 50 # 45-10", "1995-04-12"
        )
        client_model.create(
            "1040987654", "María", "Gómez", "Carrera 53 # 75-80", "1998-08-25"
        )
        client_model.create(
            "1040555444", "Luisa", "Martínez", "Calle 82 # 51B-30", "2001-01-15"
        )

        prod_model.create("PROD-001", "900123456-1", 'Monitor LG 27"', 850000)
        prod_model.create(
            "PROD-002", "900123456-1", "Teclado Mecánico RGB", 220000
        )
        prod_model.create("PROD-003", "800987654-2", "Silla Ergonómica", 650000)
        prod_model.create(
            "PROD-004", "901112233-3", "Escritorio Ajustable", 1200000
        )

        detalles_pedido_1 = [
            {
                "codigo_producto": "PROD-001",
                "cantidad": 1,
                "precio_compra": 850000,
            },
            {
                "codigo_producto": "PROD-002",
                "cantidad": 2,
                "precio_compra": 220000,
            },
        ]
        pedido_model.create_pedido("1040123456", "2026-10-15", detalles_pedido_1)

        detalles_pedido_2 = [
            {
                "codigo_producto": "PROD-003",
                "cantidad": 1,
                "precio_compra": 650000,
            }
        ]
        pedido_model.create_pedido("1040987654", "2026-10-18", detalles_pedido_2)

        logger.info("Database seeding process completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during database seeding: {e}")
        raise


if __name__ == "__main__":
    seed_database()