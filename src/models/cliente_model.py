import logging
import sqlite3
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)


class ClienteModel:
    """Handles data persistence and business logic operations for Clients (Cliente)."""

    _instance: "ClienteModel | None" = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "ClienteModel":
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

    def _validar_fecha_nacimiento(self, fecha_nacimiento: str) -> bool:
        """Valida que la fecha tenga formato YYYY-MM-DD y no sea posterior a la fecha actual (Objetivo 1)."""
        try:
            fecha_dt = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
            if fecha_dt > date.today():
                logger.warning(
                    f"Intento de registrar fecha futura: {fecha_nacimiento}"
                )
                return False
            return True
        except ValueError:
            logger.warning(f"Formato de fecha inválido: {fecha_nacimiento}")
            return False

    def create(
        self,
        identificacion: str,
        nombres: str,
        apellidos: str,
        direccion: str,
        fecha_nacimiento: str,
    ) -> bool:
        """Inserts a new client record into the database."""
        # Objetivo 1: Validación de fecha no futura
        if not self._validar_fecha_nacimiento(fecha_nacimiento):
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Objetivo 4: dirección -> direccion
                cursor.execute(
                    """
                    INSERT INTO Cliente (identificacion, nombres, apellidos, direccion, fecha_nacimiento)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (identificacion, nombres, apellidos, direccion, fecha_nacimiento),
                )
                conn.commit()
                logger.info(f"Client successfully created with ID: {identificacion}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error creating client {identificacion}: {e}")
            return False

    def get_all(self) -> list[dict[str, Any]]:
        """Retrieves all registered clients from the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Objetivo 4: dirección -> direccion
                cursor.execute(
                    "SELECT identificacion, nombres, apellidos, direccion, fecha_nacimiento FROM Cliente"
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving clients: {e}")
            return []

    def get_by_id(self, identificacion: str) -> dict[str, Any] | None:
        """Retrieves a single client by their identification."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Objetivo 4: dirección -> direccion
                cursor.execute(
                    "SELECT identificacion, nombres, apellidos, direccion, fecha_nacimiento FROM Cliente WHERE identificacion = ?",
                    (identificacion,),
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving client {identificacion}: {e}")
            return None

    def update(
        self,
        identificacion: str,
        nombres: str | None = None,
        apellidos: str | None = None,
        direccion: str | None = None,
        fecha_nacimiento: str | None = None,
    ) -> bool:
        """Updates an existing client's information."""
        current = self.get_by_id(identificacion)
        if not current:
            logger.warning(f"Client with ID {identificacion} not found for update.")
            return False

        new_nombres = nombres if nombres is not None else current["nombres"]
        new_apellidos = apellidos if apellidos is not None else current["apellidos"]
        new_direccion = direccion if direccion is not None else current["direccion"]
        new_fecha = (
            fecha_nacimiento
            if fecha_nacimiento is not None
            else current["fecha_nacimiento"]
        )

        # Objetivo 1: Validación de fecha no futura
        if fecha_nacimiento is not None and not self._validar_fecha_nacimiento(new_fecha):
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Objetivo 4: dirección -> direccion
                cursor.execute(
                    """
                    UPDATE Cliente
                    SET nombres = ?, apellidos = ?, direccion = ?, fecha_nacimiento = ?
                    WHERE identificacion = ?
                    """,
                    (new_nombres, new_apellidos, new_direccion, new_fecha, identificacion),
                )
                conn.commit()
                logger.info(f"Client with ID {identificacion} successfully updated.")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error updating client {identificacion}: {e}")
            return False

    def delete(self, identificacion: str) -> bool:
        """Deletes a client by their identification."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM Cliente WHERE identificacion = ?", (identificacion,)
                )
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Client with ID {identificacion} successfully deleted.")
                    return True
                logger.warning(f"Client with ID {identificacion} not found for deletion.")
                return False
        except sqlite3.Error as e:
            logger.error(
                f"Error deleting client {identificacion} (likely restricted by foreign keys): {e}"
            )
            return False