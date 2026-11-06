import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Iterator

from .models import TYPES_OPERATION


class BudgetDatabase:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_table()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except sqlite3.Error:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _create_table(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL CHECK (type IN ('Revenu', 'Dépense')),
                    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                    operation_date TEXT NOT NULL,
                    category TEXT NOT NULL CHECK (length(trim(category)) > 0),
                    note TEXT NOT NULL DEFAULT ''
                )"""
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_operations_date ON operations(operation_date)"
            )

    def add_operation(
        self, operation_type: str, amount_cents: int, operation_date: str, category: str, note: str = ""
    ) -> int:
        self._validate_operation(operation_type, amount_cents, operation_date, category)
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO operations (type, amount_cents, operation_date, category, note) "
                "VALUES (?, ?, ?, ?, ?)",
                (operation_type, amount_cents, operation_date, category.strip(), note.strip()),
            )
            return int(cursor.lastrowid)

    def update_operation(
        self,
        operation_id: int,
        operation_type: str,
        amount_cents: int,
        operation_date: str,
        category: str,
        note: str = "",
    ) -> None:
        self._validate_operation(operation_type, amount_cents, operation_date, category)
        with self._connect() as connection:
            connection.execute(
                "UPDATE operations SET type = ?, amount_cents = ?, operation_date = ?, "
                "category = ?, note = ? WHERE id = ?",
                (operation_type, amount_cents, operation_date, category.strip(), note.strip(), operation_id),
            )

    def delete_operation(self, operation_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM operations WHERE id = ?", (operation_id,))

    @staticmethod
    def _validate_operation(
        operation_type: str, amount_cents: int, operation_date: str, category: str
    ) -> None:
        if operation_type not in TYPES_OPERATION:
            raise ValueError("Choisissez un type d’opération valide.")
        if not isinstance(amount_cents, int) or amount_cents <= 0:
            raise ValueError("Le montant doit être supérieur à zéro.")
        try:
            date.fromisoformat(operation_date)
        except ValueError as error:
            raise ValueError("La date de l’opération doit être une date valide au format AAAA-MM-JJ.") from error
        if not category.strip():
            raise ValueError("La catégorie ne peut pas être vide.")

    def list_operations(
        self,
        year: int | None = None,
        month: int | None = None,
        operation_type: str = "Toutes",
        category: str = "Toutes",
        search: str = "",
    ) -> list[sqlite3.Row]:
        conditions = []
        values: list[object] = []
        if year is not None:
            conditions.append("substr(operation_date, 1, 4) = ?")
            values.append(f"{year:04d}")
        if month is not None:
            conditions.append("substr(operation_date, 6, 2) = ?")
            values.append(f"{month:02d}")
        if operation_type in TYPES_OPERATION:
            conditions.append("type = ?")
            values.append(operation_type)
        if category != "Toutes":
            conditions.append("category = ?")
            values.append(category)
        if search.strip():
            conditions.append("(category LIKE ? OR note LIKE ?)")
            pattern = f"%{search.strip()}%"
            values.extend((pattern, pattern))
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self._connect() as connection:
            # Les filtres restent des paramètres séparés de la requête SQL.
            return connection.execute(
                f"SELECT id, type, amount_cents, operation_date, category, note "
                f"FROM operations {where_clause} ORDER BY operation_date DESC, id DESC",
                values,
            ).fetchall()

    def monthly_summary(self, year: int, month: int) -> dict[str, int]:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT
                    COALESCE(SUM(CASE WHEN type = 'Revenu' THEN amount_cents ELSE 0 END), 0) AS income,
                    COALESCE(SUM(CASE WHEN type = 'Dépense' THEN amount_cents ELSE 0 END), 0) AS expenses
                FROM operations
                WHERE substr(operation_date, 1, 4) = ? AND substr(operation_date, 6, 2) = ?""",
                (f"{year:04d}", f"{month:02d}"),
            ).fetchone()
        income = int(row["income"])
        expenses = int(row["expenses"])
        return {"income": income, "expenses": expenses, "balance": income - expenses}

    def expenses_by_category(self, year: int, month: int) -> list[sqlite3.Row]:
        with self._connect() as connection:
            return connection.execute(
                """SELECT category, SUM(amount_cents) AS total_cents
                FROM operations
                WHERE type = 'Dépense' AND substr(operation_date, 1, 4) = ?
                    AND substr(operation_date, 6, 2) = ?
                GROUP BY category ORDER BY total_cents DESC, category COLLATE NOCASE""",
                (f"{year:04d}", f"{month:02d}"),
            ).fetchall()

    def categories(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT category FROM operations ORDER BY category COLLATE NOCASE"
            ).fetchall()
        return [str(row["category"]) for row in rows]
