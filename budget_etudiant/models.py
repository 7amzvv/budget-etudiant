from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


TYPES_OPERATION = ("Revenu", "Dépense")


def parse_amount(value: str) -> int:
    normalized = value.strip().replace(" ", "").replace("\u202f", "").replace(",", ".")
    if not normalized:
        raise ValueError("Saisissez un montant.")
    try:
        amount = Decimal(normalized)
    except InvalidOperation as error:
        raise ValueError("Le montant doit être un nombre valide.") from error
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Le montant doit être supérieur à zéro.")
    # Garder les montants en centimes entiers évite les imprécisions des flottants.
    amount_cents = int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if amount_cents <= 0:
        raise ValueError("Le montant minimal est de 0,01 €.")
    return amount_cents


def parse_date(value: str) -> str:
    date_text = value.strip()
    try:
        parsed = datetime.strptime(date_text, "%d/%m/%Y")
    except ValueError as error:
        raise ValueError("La date doit être valide et au format JJ/MM/AAAA.") from error
    return parsed.strftime("%Y-%m-%d")


def display_date(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")


def format_amount(amount_cents: int) -> str:
    amount = Decimal(amount_cents) / 100
    return f"{amount:,.2f} €".replace(",", " ").replace(".", ",")
