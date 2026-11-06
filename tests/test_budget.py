import tempfile
import unittest
from pathlib import Path

from budget_etudiant.database import BudgetDatabase
from budget_etudiant.models import display_date, format_amount, parse_amount, parse_date


class BudgetModelTests(unittest.TestCase):
    def test_parse_amount_supports_french_decimal_separator(self):
        self.assertEqual(parse_amount("1 234,56"), 123456)

    def test_parse_amount_rejects_empty_zero_and_invalid_values(self):
        for value in ("", "0", "-4", "abc"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_amount(value)

    def test_date_round_trip_and_invalid_day(self):
        self.assertEqual(parse_date("06/11/2026"), "2026-11-06")
        self.assertEqual(display_date("2026-11-06"), "06/11/2026")
        with self.assertRaises(ValueError):
            parse_date("31/02/2026")

    def test_amount_display(self):
        self.assertEqual(format_amount(123456), "1 234,56 €")


class BudgetDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.database = BudgetDatabase(Path(self.temp_dir.name) / "budget.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_monthly_summary_and_category_totals(self):
        self.database.add_operation("Revenu", 100000, "2026-11-01", "Salaire")
        self.database.add_operation("Dépense", 1250, "2026-11-02", "Alimentation")
        self.database.add_operation("Dépense", 750, "2026-11-03", "Transport")
        self.database.add_operation("Dépense", 5000, "2026-10-03", "Loyer")
        self.assertEqual(self.database.monthly_summary(2026, 11), {"income": 100000, "expenses": 2000, "balance": 98000})
        totals = self.database.expenses_by_category(2026, 11)
        self.assertEqual([(row["category"], row["total_cents"]) for row in totals], [("Alimentation", 1250), ("Transport", 750)])

    def test_update_delete_and_filters(self):
        operation_id = self.database.add_operation("Dépense", 2500, "2026-11-06", "Transport", "Bus")
        self.database.update_operation(operation_id, "Dépense", 3000, "2026-11-07", "Transport", "Train")
        rows = self.database.list_operations(2026, 11, "Dépense", "Transport", "Train")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["amount_cents"], 3000)
        self.database.delete_operation(operation_id)
        self.assertEqual(self.database.list_operations(), [])

    def test_data_is_kept_after_reopening_database(self):
        self.database.add_operation("Revenu", 85000, "2026-11-06", "Aide")
        reopened = BudgetDatabase(Path(self.temp_dir.name) / "budget.db")
        self.assertEqual(len(reopened.list_operations()), 1)
        self.assertEqual(reopened.monthly_summary(2026, 11)["income"], 85000)


if __name__ == "__main__":
    unittest.main()
