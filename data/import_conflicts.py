"""
import_conflicts.py
───────────────────
Imports manually curated ingredient conflict pairs into the database.
Run from project root: python data/import_conflicts.py

IMPORTANT: Run this AFTER import_concerns.py and import_products.py
           so that ingredients already exist in the database.

What this does:
  1. Reads data/conflicts.csv
  2. Looks up each ingredient by name
  3. Creates IngredientConflict rows (always stores lower ID as ingredient_1)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.database import SessionLocal, engine, Base
from app.models.models import Ingredient, IngredientConflict


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        df = pd.read_csv("data/conflicts.csv")
        print(f"Loaded {len(df)} conflict pairs from conflicts.csv")

        added = 0
        skipped = 0

        for _, row in df.iterrows():
            name_1 = str(row["ingredient_1"]).strip().lower()
            name_2 = str(row["ingredient_2"]).strip().lower()
            severity = str(row["severity"]).strip().lower()

            # ── Look up ingredients (case-insensitive) ────────────────────
            ing_1 = db.query(Ingredient).filter(
                Ingredient.name.ilike(name_1)
            ).first()

            ing_2 = db.query(Ingredient).filter(
                Ingredient.name.ilike(name_2)
            ).first()

            # If ingredient doesn't exist yet, create it
            # (some conflict ingredients may not be in the product dataset)
            if not ing_1:
                ing_1 = Ingredient(name=name_1, irritation_level="high")
                db.add(ing_1)
                db.flush()
                print(f"   Created missing ingredient: {name_1}")

            if not ing_2:
                ing_2 = Ingredient(name=name_2, irritation_level="high")
                db.add(ing_2)
                db.flush()
                print(f"   Created missing ingredient: {name_2}")

            # ── Always store lower ID as ingredient_1 (prevents duplicates) ─
            id_a = min(ing_1.id, ing_2.id)
            id_b = max(ing_1.id, ing_2.id)

            # Check if this pair already exists
            existing = db.query(IngredientConflict).filter(
                IngredientConflict.ingredient_1_id == id_a,
                IngredientConflict.ingredient_2_id == id_b
            ).first()

            if existing:
                print(f"   Skipping duplicate: {name_1} + {name_2}")
                skipped += 1
                continue

            conflict = IngredientConflict(
                ingredient_1_id=id_a,
                ingredient_2_id=id_b,
                severity=severity
            )
            db.add(conflict)
            added += 1

        db.commit()
        print(f" Done!")
        print(f"   Conflicts added:   {added}")
        print(f"   Duplicates skipped: {skipped}")

    except Exception as e:
        db.rollback()
        print(f" Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()