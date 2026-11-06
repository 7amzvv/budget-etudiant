# Budget étudiant

Application de bureau pour suivre ses revenus et ses dépenses, consulter son solde mensuel et repérer les catégories qui pèsent le plus dans son budget.

## Fonctionnalités

- Ajouter, modifier et supprimer des revenus ou des dépenses.
- Enregistrer pour chaque opération un montant, une date, une catégorie et une note facultative.
- Voir les revenus, dépenses et le solde du mois sélectionné.
- Filtrer l’historique par mois, année, type et catégorie, ou rechercher dans les catégories et les notes.
- Comparer les dépenses du mois par catégorie.
- Conserver les opérations dans une base SQLite locale.
- Afficher les montants en euros avec des centimes et accepter la virgule décimale française.
- Signaler les montants et dates invalides dans l’interface.

## Technologies

- Python 3.10 ou ultérieur
- Tkinter pour l’interface graphique
- SQLite, inclus avec Python

Aucune dépendance externe n’est nécessaire. Tkinter doit être inclus dans l’installation de Python.

## Installation et lancement

Installez Python 3.10 ou une version ultérieure, puis ouvrez un terminal dans le dossier du projet :

```powershell
cd budget-etudiant
python --version
python -m budget_etudiant.app
```

Sous Windows, si la commande `python` n’est pas reconnue, utilisez l’interpréteur Python installé en précisant son chemin complet.

La base `budget.db` est créée automatiquement dans le dossier du projet au premier lancement.

## Exemple d’utilisation

1. Cliquez sur **Ajouter une opération**.
2. Choisissez **Revenu**, saisissez `850,00`, la date du versement et la catégorie `Aide`.
3. Ajoutez une dépense de `42,50` dans la catégorie `Alimentation`.
4. Vérifiez le solde du mois, puis filtrez l’historique par type ou catégorie.

## Organisation des fichiers

```text
budget-etudiant/
├── budget_etudiant/
│   ├── app.py          # Interface Tkinter
│   ├── database.py     # Enregistrement et calculs SQLite
│   └── models.py       # Validation et formatage des montants et dates
├── tests/
│   └── test_budget.py
├── .gitignore
└── README.md
```

## Notions informatiques travaillées

- Interface événementielle avec Tkinter et widgets `ttk`.
- Modélisation d’opérations et validation des entrées.
- Requêtes SQL paramétrées, agrégations, filtres et regroupement par catégorie.
- Persistance locale avec SQLite.
- Calcul monétaire en centimes entiers afin d’éviter les imprécisions des nombres flottants.
- Tests unitaires avec `unittest`.

## Vérifications et limites

- Les 7 tests `unittest` passent : validation des montants et dates, calcul des totaux, filtres, modification, suppression et réouverture de la base.
- La compilation syntaxique de tous les modules Python passe.
- L’application Tkinter a été lancée dans l’environnement de développement.
- Les opérations sont locales à cet ordinateur ; aucune synchronisation entre appareils ni export de relevé n’est prévu dans cette première version.
- Le solde affiché correspond aux revenus moins les dépenses du mois sélectionné. Il ne représente pas automatiquement le solde bancaire reporté des mois précédents.

## Crédit

Projet réalisé par Hamza FADLI.
