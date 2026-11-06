"""Fixed reference data shared by Alembic migrations, the seed script and app startup.

Single source of truth for the base data that must always exist in the database.
"""

BASE_CATEGORIES: list[str] = [
    "Entrantes",
    "Primeros",
    "Segundos",
    "Postres",
    "Bebidas",
]

# Regulation (EU) No 1169/2011, Annex II: allergens that must be declared.
EU_ALLERGENS: list[str] = [
    "Gluten",
    "Crustáceos",
    "Huevos",
    "Pescado",
    "Cacahuetes",
    "Soja",
    "Lácteos",
    "Frutos de cáscara",
    "Apio",
    "Mostaza",
    "Sésamo",
    "Dióxido de azufre y sulfitos",
    "Altramuces",
    "Moluscos",
]
