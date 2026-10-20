import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


class ReporteModel:
    """Handles reporting and analytical queries joining multiple entities."""

    _instance: "ReporteModel | None" = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "ReporteModel":
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

    def clientes_con_conteo_pedidos(self) -> list[dict[str, Any]]:
        """Retrieves clients along with the total count of orders they have placed."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT c.identificacion, c.nombres, c.apellidos, COUNT(p.id_pedido) AS total_pedidos
                    FROM Cliente c
                    LEFT JOIN Pedido p ON c.identificacion = p.id_cliente
                    GROUP BY c.identificacion, c.nombres, c.apellidos
                    """
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching clients order counts: {e}")
            return []

    def clientes_sin_pedidos(self) -> list[dict[str, Any]]:
        """Retrieves clients who have not placed any orders."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Objetivo 4: dirección -> direccion
                cursor.execute(
                    """
                    SELECT c.identificacion, c.nombres, c.apellidos, c.direccion, c.fecha_nacimiento
                    FROM Cliente c
                    LEFT JOIN Pedido p ON c.identificacion = p.id_cliente
                    WHERE p.id_pedido IS NULL
                    """
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching clients without orders: {e}")
            return []

    def detalle_completo_compras(self) -> list[dict[str, Any]]:
        """Retrieves detailed purchase records joining client, product, and supplier data."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        c.nombres || ' ' || c.apellidos AS nombre_cliente,
                        pr.nombre AS nombre_producto,
                        dp.cantidad,
                        dp.precio_compra,
                        prov.nombre AS nombre_proveedor
                    FROM Pedido p
                    JOIN Cliente c ON p.id_cliente = c.identificacion
                    JOIN Detalle_pedido dp ON p.id_pedido = dp.id_pedido
                    JOIN Producto pr ON dp.codigo_producto = pr.codigo
                    JOIN Proveedor prov ON pr.nit_proveedor = prov.nit
                    """
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching complete purchase details: {e}")
            return []

    def proveedores_con_productos(self) -> list[dict[str, Any]]:
        """Retrieves suppliers along with their supplied products."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        prov.nit,
                        prov.nombre AS nombre_proveedor,
                        prov.direccion,
                        pr.codigo AS codigo_producto,
                        pr.nombre AS nombre_producto,
                        pr.precio_unitario
                    FROM Proveedor prov
                    LEFT JOIN Producto pr ON prov.nit = pr.nit_proveedor
                    """
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching suppliers with products: {e}")
            return []