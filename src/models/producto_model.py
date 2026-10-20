import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


class ProductoModel:
    """Handles data persistence and business logic operations for Products (Producto)."""

    _instance: "ProductoModel | None" = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "ProductoModel":
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

    def create(self, codigo: str, nit_proveedor: str, nombre: str, precio_unitario: int) -> bool:
        """Inserts a new product record into the database.

        Args:
            codigo (str): Primary key identifier for the product.
            nit_proveedor (str): NIT of the supplier providing the product.
            nombre (str): Name of the product.
            precio_unitario (int): Unit price of the product in COP.

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        precio_entero = round(float(precio_unitario))

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO Producto (codigo, nit_proveedor, nombre, precio_unitario)
                    VALUES (?, ?, ?, ?)
                    """,
                    (codigo, nit_proveedor, nombre, precio_entero),
                )
                conn.commit()
                logger.info(f"Product successfully created with code: {codigo}")
                return True
        except (sqlite3.Error, ValueError) as e:
            logger.error(f"Error creating product {codigo}: {e}")
            return False

    def get_all(self) -> list[dict[str, Any]]:
        """Retrieves all registered products from the database.

        Returns:
            list[dict[str, Any]]: A list of dictionaries representing each product.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT codigo, nit_proveedor, nombre, precio_unitario FROM Producto"
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving products: {e}")
            return []

    def get_by_id(self, codigo: str) -> dict[str, Any] | None:
        """Retrieves a single product by its code.

        Args:
            codigo (str): The code of the product.

        Returns:
            dict[str, Any] | None: Product data dictionary or None if not found.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT codigo, nit_proveedor, nombre, precio_unitario FROM Producto WHERE codigo = ?",
                    (codigo,),
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving product {codigo}: {e}")
            return None

    def update(
        self,
        codigo: str,
        nit_proveedor: str | None = None,
        nombre: str | None = None,
        precio_unitario: int | None = None,
    ) -> bool:
        """Updates an existing product's information.

        Args:
            codigo (str): The code of the product to update.
            nit_proveedor (str | None, optional): New supplier NIT.
            nombre (str | None, optional): New product name.
            precio_unitario (int | None, optional): New unit price in COP.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        current = self.get_by_id(codigo)
        if not current:
            logger.warning(f"Product with code {codigo} not found for update.")
            return False

        new_nit_proveedor = (
            nit_proveedor if nit_proveedor is not None else current["nit_proveedor"]
        )
        new_nombre = nombre if nombre is not None else current["nombre"]
        
        if precio_unitario is not None:
            new_precio = round(float(precio_unitario))
        else:
            new_precio = current["precio_unitario"]

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE Producto
                    SET nit_proveedor = ?, nombre = ?, precio_unitario = ?
                    WHERE codigo = ?
                    """,
                    (new_nit_proveedor, new_nombre, new_precio, codigo),
                )
                conn.commit()
                logger.info(f"Product with code {codigo} successfully updated.")
                return True
        except (sqlite3.Error, ValueError) as e:
            logger.error(f"Error updating product {codigo}: {e}")
            return False

    def delete(self, codigo: str) -> bool:
        """Deletes a product by its code.

        Args:
            codigo (str): The code of the product to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Producto WHERE codigo = ?", (codigo,))
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Product with code {codigo} successfully deleted.")
                    return True
                logger.warning(f"Product with code {codigo} not found for deletion.")
                return False
        except sqlite3.Error as e:
            logger.error(
                f"Error deleting product {codigo} (likely restricted by foreign keys): {e}"
            )
            return False