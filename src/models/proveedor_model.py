import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


class ProveedorModel:
    """Handles data persistence and business logic operations for Suppliers (Proveedor)."""

    _instance: "ProveedorModel | None" = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "ProveedorModel":
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

    def create(self, nit: str, nombre: str, direccion: str) -> bool:
        """Inserts a new supplier record into the database.

        Args:
            nit (str): Primary key identifier for the supplier.
            nombre (str): Name of the supplier.
            direccion (str): Physical address of the supplier.

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO Proveedor (nit, nombre, direccion)
                    VALUES (?, ?, ?)
                    """,
                    (nit, nombre, direccion),
                )
                conn.commit()
                logger.info(f"Supplier successfully created with NIT: {nit}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error creating supplier {nit}: {e}")
            return False

    def get_all(self) -> list[dict[str, Any]]:
        """Retrieves all registered suppliers from the database.

        Returns:
            list[dict[str, Any]]: A list of dictionaries representing each supplier.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nit, nombre, direccion FROM Proveedor")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving suppliers: {e}")
            return []

    def get_by_id(self, nit: str) -> dict[str, Any] | None:
        """Retrieves a single supplier by their NIT.

        Args:
            nit (str): The NIT of the supplier.

        Returns:
            dict[str, Any] | None: Supplier data dictionary or None if not found.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT nit, nombre, direccion FROM Proveedor WHERE nit = ?", (nit,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving supplier {nit}: {e}")
            return None

    def update(self, nit: str, nombre: str | None = None, direccion: str | None = None) -> bool:
        """Updates an existing supplier's information.

        Args:
            nit (str): The NIT of the supplier to update.
            nombre (str | None, optional): New name.
            direccion (str | None, optional): New address.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        current = self.get_by_id(nit)
        if not current:
            logger.warning(f"Supplier with NIT {nit} not found for update.")
            return False

        new_nombre = nombre if nombre is not None else current["nombre"]
        new_direccion = direccion if direccion is not None else current["direccion"]

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE Proveedor
                    SET nombre = ?, direccion = ?
                    WHERE nit = ?
                    """,
                    (new_nombre, new_direccion, nit),
                )
                conn.commit()
                logger.info(f"Supplier with NIT {nit} successfully updated.")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error updating supplier {nit}: {e}")
            return False

    def delete(self, nit: str) -> bool:
        """Deletes a supplier by their NIT.

        Args:
            nit (str): The NIT of the supplier to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Proveedor WHERE nit = ?", (nit,))
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Supplier with NIT {nit} successfully deleted.")
                    return True
                logger.warning(f"Supplier with NIT {nit} not found for deletion.")
                return False
        except sqlite3.Error as e:
            logger.error(
                f"Error deleting supplier {nit} (likely restricted by foreign keys): {e}"
            )
            return False