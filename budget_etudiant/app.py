import sqlite3
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk

from .database import BudgetDatabase
from .models import TYPES_OPERATION, display_date, format_amount, parse_amount, parse_date


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "budget.db"
MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]
CATEGORIES_SUGGESTIONS = [
    "Alimentation",
    "Aide",
    "Études",
    "Loisirs",
    "Logement",
    "Santé",
    "Salaire",
    "Transport",
    "Autre",
]


class BudgetApp:
    def __init__(self, root: tk.Tk, database: BudgetDatabase):
        self.root = root
        self.database = database
        self.root.title("Budget étudiant")
        self.root.geometry("1120x760")
        self.root.minsize(860, 620)
        self.root.configure(background="#f3f5f9")
        self._configure_styles()
        self._build_interface()
        self.refresh()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#f3f5f9")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f3f5f9", foreground="#202938", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 23, "bold"), foreground="#172033")
        style.configure("Subtitle.TLabel", foreground="#657187")
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#657187", font=("Segoe UI", 9))
        style.configure("CardValue.TLabel", background="#ffffff", foreground="#172033", font=("Segoe UI", 17, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8))
        style.configure("Treeview", rowheight=32, font=("Segoe UI", 10), background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#e9edf4")
        style.map("Treeview", background=[("selected", "#dce8ff")], foreground=[("selected", "#172033")])

    def _build_interface(self) -> None:
        outer = ttk.Frame(self.root, padding=(24, 20))
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 18))
        title_block = ttk.Frame(header)
        title_block.pack(side="left", fill="x", expand=True)
        ttk.Label(title_block, text="Budget étudiant", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_block, text="Visualisez vos revenus et vos dépenses, mois par mois.", style="Subtitle.TLabel").pack(anchor="w", pady=(3, 0))
        ttk.Button(header, text="＋  Ajouter une opération", style="Primary.TButton", command=self.add_operation).pack(side="right", anchor="center")

        summary = ttk.Frame(outer)
        summary.pack(fill="x", pady=(0, 18))
        self.income_value = self._summary_card(summary, "Revenus du mois", 0)
        self.expense_value = self._summary_card(summary, "Dépenses du mois", 1)
        self.balance_value = self._summary_card(summary, "Solde du mois", 2)

        main = ttk.Frame(outer)
        main.pack(fill="both", expand=True)
        history_panel = ttk.Frame(main, style="Card.TFrame", padding=16)
        history_panel.pack(side="left", fill="both", expand=True, padx=(0, 12))
        side_panel = ttk.Frame(main, style="Card.TFrame", padding=16, width=255)
        side_panel.pack(side="right", fill="y")
        side_panel.pack_propagate(False)

        ttk.Label(history_panel, text="Historique", font=("Segoe UI", 14, "bold"), background="#ffffff").pack(anchor="w", pady=(0, 12))
        filters = ttk.Frame(history_panel, style="Card.TFrame")
        filters.pack(fill="x", pady=(0, 12))
        today = date.today()
        self.month_var = tk.StringVar(value=MONTHS[today.month - 1])
        self.year_var = tk.StringVar(value=str(today.year))
        self.type_filter = tk.StringVar(value="Toutes")
        self.category_filter = tk.StringVar(value="Toutes")
        self.search_var = tk.StringVar()
        ttk.Label(filters, text="Mois", background="#ffffff").grid(row=0, column=0, sticky="w", padx=(0, 5))
        month_box = ttk.Combobox(filters, textvariable=self.month_var, values=MONTHS, width=12, state="readonly")
        month_box.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(filters, text="Année", background="#ffffff").grid(row=0, column=1, sticky="w", padx=(0, 5))
        year_values = [str(year) for year in range(today.year - 5, today.year + 6)]
        year_box = ttk.Combobox(filters, textvariable=self.year_var, values=year_values, width=7, state="readonly")
        year_box.grid(row=1, column=1, sticky="ew", padx=(0, 8))
        ttk.Label(filters, text="Type", background="#ffffff").grid(row=0, column=2, sticky="w", padx=(0, 5))
        type_box = ttk.Combobox(filters, textvariable=self.type_filter, values=["Toutes", *TYPES_OPERATION], width=11, state="readonly")
        type_box.grid(row=1, column=2, sticky="ew", padx=(0, 8))
        ttk.Label(filters, text="Catégorie", background="#ffffff").grid(row=0, column=3, sticky="w", padx=(0, 5))
        self.category_box = ttk.Combobox(filters, textvariable=self.category_filter, values=["Toutes"], width=14, state="readonly")
        self.category_box.grid(row=1, column=3, sticky="ew", padx=(0, 8))
        ttk.Label(filters, text="Rechercher", background="#ffffff").grid(row=0, column=4, sticky="w", padx=(0, 5))
        search_entry = ttk.Entry(filters, textvariable=self.search_var, width=17)
        search_entry.grid(row=1, column=4, sticky="ew")
        filters.columnconfigure(4, weight=1)
        for control in (month_box, year_box, type_box, self.category_box):
            control.bind("<<ComboboxSelected>>", self._filters_changed)
        year_box.bind("<Return>", self._filters_changed)
        search_entry.bind("<KeyRelease>", self._filters_changed)

        table_frame = ttk.Frame(history_panel, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)
        columns = ("date", "type", "category", "note", "amount")
        self.operations_table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = (("date", "Date", 95), ("type", "Type", 80), ("category", "Catégorie", 125), ("note", "Note", 160), ("amount", "Montant", 105))
        for column, heading, width in headings:
            self.operations_table.heading(column, text=heading)
            self.operations_table.column(column, width=width, anchor="e" if column == "amount" else "w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.operations_table.yview)
        self.operations_table.configure(yscrollcommand=scrollbar.set)
        self.operations_table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.operations_table.tag_configure("income", foreground="#12805c")
        self.operations_table.tag_configure("expense", foreground="#b54040")
        self.operations_table.bind("<Double-1>", lambda _event: self.edit_operation())
        actions = ttk.Frame(history_panel, style="Card.TFrame")
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Modifier la sélection", command=self.edit_operation).pack(side="left")
        ttk.Button(actions, text="Supprimer la sélection", command=self.delete_operation).pack(side="left", padx=(8, 0))
        self.count_label = ttk.Label(actions, text="", background="#ffffff", foreground="#657187")
        self.count_label.pack(side="right")

        ttk.Label(side_panel, text="Dépenses par catégorie", font=("Segoe UI", 13, "bold"), background="#ffffff", wraplength=220).pack(anchor="w", pady=(0, 4))
        self.category_period_label = ttk.Label(side_panel, text="", background="#ffffff", foreground="#657187")
        self.category_period_label.pack(anchor="w", pady=(0, 12))
        self.category_table = ttk.Treeview(side_panel, columns=("category", "total"), show="headings", height=12)
        self.category_table.heading("category", text="Catégorie")
        self.category_table.heading("total", text="Total")
        self.category_table.column("category", width=125, anchor="w")
        self.category_table.column("total", width=85, anchor="e")
        self.category_table.pack(fill="x")
        self.category_empty = ttk.Label(side_panel, text="Aucune dépense pour ce mois.", background="#ffffff", foreground="#657187", wraplength=220)
        self.category_empty.pack(anchor="w", pady=(8, 0))

    @staticmethod
    def _summary_card(parent: ttk.Frame, label: str, column: int) -> ttk.Label:
        card = ttk.Frame(parent, style="Card.TFrame", padding=(16, 12))
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0 if column == 2 else 8))
        ttk.Label(card, text=label, style="CardTitle.TLabel").pack(anchor="w")
        value = ttk.Label(card, text="0,00 €", style="CardValue.TLabel")
        value.pack(anchor="w", pady=(4, 0))
        parent.columnconfigure(column, weight=1)
        return value

    def _selected_period(self) -> tuple[int, int]:
        year = int(self.year_var.get().strip())
        month = MONTHS.index(self.month_var.get()) + 1
        return year, month

    def _filters_changed(self, _event: tk.Event | None = None) -> None:
        self.refresh()

    def refresh(self) -> None:
        try:
            year, month = self._selected_period()
        except (ValueError, IndexError):
            return
        summary = self.database.monthly_summary(year, month)
        self.income_value.configure(text=format_amount(summary["income"]))
        self.expense_value.configure(text=format_amount(summary["expenses"]))
        self.balance_value.configure(text=format_amount(summary["balance"]))
        self.balance_value.configure(foreground="#12805c" if summary["balance"] >= 0 else "#b54040")

        categories = ["Toutes", *self.database.categories()]
        self.category_box.configure(values=categories)
        if self.category_filter.get() not in categories:
            self.category_filter.set("Toutes")
        rows = self.database.list_operations(
            year,
            month,
            self.type_filter.get(),
            self.category_filter.get(),
            self.search_var.get(),
        )
        self.operations_table.delete(*self.operations_table.get_children())
        for row in rows:
            tag = "income" if row["type"] == "Revenu" else "expense"
            self.operations_table.insert(
                "", "end", iid=str(row["id"]),
                values=(display_date(row["operation_date"]), row["type"], row["category"], row["note"], format_amount(row["amount_cents"])),
                tags=(tag,),
            )
        self.count_label.configure(text=f"{len(rows)} opération(s)")
        self.category_period_label.configure(text=f"{MONTHS[month - 1]} {year}")
        category_rows = self.database.expenses_by_category(year, month)
        self.category_table.delete(*self.category_table.get_children())
        for row in category_rows:
            self.category_table.insert("", "end", values=(row["category"], format_amount(row["total_cents"])))
        if category_rows:
            self.category_empty.pack_forget()
        else:
            self.category_empty.pack(anchor="w", pady=(8, 0))

    def add_operation(self) -> None:
        self._open_operation_form()

    def _selected_operation_id(self) -> int | None:
        selected = self.operations_table.selection()
        if not selected:
            messagebox.showinfo("Aucune sélection", "Sélectionnez une opération dans l’historique.", parent=self.root)
            return None
        return int(selected[0])

    def edit_operation(self) -> None:
        operation_id = self._selected_operation_id()
        if operation_id is None:
            return
        row = next((item for item in self.database.list_operations() if item["id"] == operation_id), None)
        if row is not None:
            self._open_operation_form(row)

    def delete_operation(self) -> None:
        operation_id = self._selected_operation_id()
        if operation_id is None:
            return
        if messagebox.askyesno("Supprimer l’opération", "Cette opération sera supprimée. Continuer ?", parent=self.root):
            self.database.delete_operation(operation_id)
            self.refresh()

    def _open_operation_form(self, operation: sqlite3.Row | None = None) -> None:
        is_edit = operation is not None
        dialog = tk.Toplevel(self.root)
        dialog.title("Modifier une opération" if is_edit else "Nouvelle opération")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.configure(background="#f3f5f9")
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Modifier l’opération" if is_edit else "Ajouter une opération", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        operation_type = tk.StringVar(value=operation["type"] if is_edit else "Dépense")
        amount = tk.StringVar(value=f"{operation['amount_cents'] / 100:.2f}".replace(".", ",") if is_edit else "")
        operation_date = tk.StringVar(value=display_date(operation["operation_date"]) if is_edit else date.today().strftime("%d/%m/%Y"))
        category = tk.StringVar(value=operation["category"] if is_edit else "")
        note = tk.StringVar(value=operation["note"] if is_edit else "")
        fields = [
            ("Type", ttk.Combobox(frame, textvariable=operation_type, values=TYPES_OPERATION, state="readonly", width=34)),
            ("Montant (€)", ttk.Entry(frame, textvariable=amount, width=37)),
            ("Date (JJ/MM/AAAA)", ttk.Entry(frame, textvariable=operation_date, width=37)),
            ("Catégorie", ttk.Combobox(frame, textvariable=category, values=CATEGORIES_SUGGESTIONS + self.database.categories(), width=34)),
            ("Note (facultative)", ttk.Entry(frame, textvariable=note, width=37)),
        ]
        for index, (label, widget) in enumerate(fields, start=1):
            ttk.Label(frame, text=label).grid(row=index, column=0, sticky="w", pady=6, padx=(0, 12))
            widget.grid(row=index, column=1, sticky="ew", pady=6)
        button_row = ttk.Frame(frame)
        button_row.grid(row=6, column=0, columnspan=2, sticky="e", pady=(14, 0))

        def save() -> None:
            try:
                amount_cents = parse_amount(amount.get())
                date_iso = parse_date(operation_date.get())
                if not category.get().strip():
                    raise ValueError("Saisissez une catégorie.")
                if len(note.get()) > 160:
                    raise ValueError("La note ne peut pas dépasser 160 caractères.")
                if is_edit:
                    self.database.update_operation(operation["id"], operation_type.get(), amount_cents, date_iso, category.get(), note.get())
                else:
                    self.database.add_operation(operation_type.get(), amount_cents, date_iso, category.get(), note.get())
            except ValueError as error:
                messagebox.showerror("Vérifiez les informations", str(error), parent=dialog)
                return
            except sqlite3.Error as error:
                messagebox.showerror("Erreur de sauvegarde", f"L’opération n’a pas pu être enregistrée : {error}", parent=dialog)
                return
            dialog.destroy()
            self.refresh()

        ttk.Button(button_row, text="Annuler", command=dialog.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(button_row, text="Enregistrer", style="Primary.TButton", command=save).pack(side="left")
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.bind("<Return>", lambda _event: save())
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        fields[1][1].focus_set()


def main() -> None:
    database = BudgetDatabase(DATABASE_PATH)
    root = tk.Tk()
    BudgetApp(root, database)
    root.mainloop()


if __name__ == "__main__":
    main()
