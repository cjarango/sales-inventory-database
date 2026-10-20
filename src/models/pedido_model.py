import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


class PedidoModel:
    """Handles data persistence and business logic operations for Orders (Pedido & Detalle_pedido)."""

    _instance: "PedidoModel | None" = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "PedidoModel":
        """Implements a Singleton pattern to ensure a single instance."""
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._initialized = False  # type: ignore[attr-defined]
            cls._instance = instance
        return cls._instance

    def __init__(self, db_path: str = "database.db") -> None:
        """Initializes the model with a target SQLite database path."""
        if getattr(self, "_initialized", False):
            return
        self.db_path = db_path
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Establishes and returns a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def create_pedido(
        self, id_cliente: str, fecha: str, detalles: list[dict[str, Any]]
    ) -> int | None:
        """Creates a new order with its details in a transactional manner."""
        if not detalles:
            logger.warning("Attempted to create an order without items.")
            return None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO Pedido (id_cliente, fecha)
                    VALUES (?, ?)
                    """,
                    (id_cliente, fecha),
                )
                pedido_id = cursor.lastrowid

                if not pedido_id:
                    raise sqlite3.Error("Failed to retrieve last inserted order ID.")

                for item in detalles:
                    # Objetivo 3: Garantizar que el precio en COP se registre como un valor entero (int)
                    precio_entero = round(float(item["precio_compra"]))

                    cursor.execute(
                        """
                        INSERT INTO Detalle_pedido (id_pedido, codigo_producto, cantidad, precio_compra)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            pedido_id,
                            item["codigo_producto"],
                            int(item["cantidad"]),
                            precio_entero,
                        ),
                    )

                conn.commit()
                logger.info(f"Order successfully created with ID: {pedido_id}")
                return pedido_id

        except (sqlite3.Error, ValueError, KeyError) as e:
            logger.error(f"Error creating order for client {id_cliente}: {e}")
            return None

    def get_all(self) -> list[dict[str, Any]]:
        """Retrieves all registered orders along with their client information."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT p.id_pedido, p.id_cliente, p.fecha,
                           c.nombres || ' ' || c.apellidos AS nombre_cliente
                    FROM Pedido p
                    JOIN Cliente c ON p.id_cliente = c.identificacion
                    """
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving orders: {e}")
            return []

    def get_by_id(self, id_pedido: int) -> dict[str, Any] | None:
        """Retrieves a single order by its ID, including its associated detail items."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id_pedido, id_cliente, fecha
                    FROM Pedido
                    WHERE id_pedido = ?
                    """,
                    (id_pedido,),
                )
                row = cursor.fetchone()
                if not row:
                    return None

                order_data = dict(row)

                cursor.execute(
                    """
                    SELECT codigo_producto, cantidad, precio_compra
                    FROM Detalle_pedido
                    WHERE id_pedido = ?
                    """,
                    (id_pedido,),
                )
                details = [dict(d_row) for d_row in cursor.fetchall()]
                order_data["detalles"] = details

                return order_data

        except sqlite3.Error as e:
            logger.error(f"Error retrieving order {id_pedido}: {e}")
            return None

    def delete(self, id_pedido: int) -> bool:
        """Deletes an order by its ID (Cascades to order details)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Pedido WHERE id_pedido = ?", (id_pedido,))
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Order with ID {id_pedido} successfully deleted.")
                    return True
                logger.warning(f"Order with ID {id_pedido} not found for deletion.")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting order {id_pedido}: {e}")
            return False