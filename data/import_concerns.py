"""
import_concerns.py
─────────────────
Imports skin concerns + recommended ingredients from the Celestia dataset.
Run from project root: python data/import_concerns.py

What this does:
  1. Reads CELESTIA_SKIN_CARE_DASTASET.csv
  2. For each unique (Skin_Type, Concern) pair → creates a SkinConcern row
  3. Parses the Ingredients column (comma/+ separated) → creates Ingredient rows
  4. Links ingredients to concerns via the concern_ingredients bridge table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.database import SessionLocal, engine, Base
from app.models.models import SkinConcern, Ingredient

# ── irritation level lookup (dermatological knowledge) ──────────────────────
# Used to set irritation_level on each ingredient at import time
IRRITATION_LOOKUP = {
    # High irritation
    "retinol": "high",
    "benzoyl peroxide": "high",
    "salicylic acid": "high",
    "glycolic acid": "high",
    "lactic acid": "high",
    "mandelic acid": "high",
    "trichloroacetic acid": "high",
    "resorcinol": "high",
    "tretinoin": "high",
    "isotretinoin": "high",

    # Medium irritation
    "aha": "medium",
    "bha": "medium",
    "vitamin c": "medium",
    "ascorbic acid": "medium",
    "niacinamide": "medium",
    "kojic acid": "medium",
    "azelaic acid": "medium",
    "alpha arbutin": "medium",
    "ferulic acid": "medium",
    "zinc pca": "medium",
    "bakuchiol": "medium",
    "peptides": "medium",

    # Low irritation (default for most)
    "hyaluronic acid": "low",
    "ceramide": "low",
    "glycerin": "low",
    "aloe vera": "low",
    "green tea extract": "low",
    "centella asiatica": "low",
    "panthenol": "low",
    "allantoin": "low",
    "squalane": "low",
    "jojoba oil": "low",
    "rosehip oil": "low",
    "vitamin e": "low",
    "tocopherol": "low",
}

def get_irritation_level(ingredient_name: str) -> str:
    """Return irritation level based on ingredient name lookup."""
    name_lower = ingredient_name.lower().strip()
    for key, level in IRRITATION_LOOKUP.items():
        if key in name_lower:
            return level
    return "low"  # default: most ingredients are low irritation


def parse_ingredients(raw: str) -> list[str]:
    """
    Parse the Ingredients column from the Celestia dataset.
    Format is: 'Zinc PCA + Benzoyl Peroxide + Salicylic Acid'
    Returns a list of clean ingredient name strings.
    """
    if pd.isna(raw):
        return []
    # Split on '+' and clean whitespace
    parts = [p.strip() for p in str(raw).split("+")]
    return [p for p in parts if p]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        df = pd.read_csv("data/CELESTIA_SKIN_CARE_DASTASET.csv")
        print(f"Loaded {len(df)} rows from Celestia dataset")

        concerns_added = 0
        ingredients_added = 0
        links_added = 0

        # Cache so we don't hit DB repeatedly for same ingredient
        ingredient_cache: dict[str, Ingredient] = {}

        for _, row in df.iterrows():
            skin_type = str(row["Skin_Type"]).strip()
            concern_name = str(row["Concern"]).strip()
            raw_ingredients = row["Ingredients"]

            # ── 1. Get or create SkinConcern ─────────────────────────────
            concern = db.query(SkinConcern).filter(
                SkinConcern.name == concern_name,
                SkinConcern.skin_type == skin_type
            ).first()

            if not concern:
                concern = SkinConcern(name=concern_name, skin_type=skin_type)
                db.add(concern)
                db.flush()  # get ID without full commit
                concerns_added += 1

            # ── 2. Parse + get or create each Ingredient ─────────────────
            ingredient_names = parse_ingredients(raw_ingredients)

            for ing_name in ingredient_names:
                ing_name_clean = ing_name.strip()
                if not ing_name_clean:
                    continue

                cache_key = ing_name_clean.lower()

                if cache_key not in ingredient_cache:
                    # Check DB first
                    existing = db.query(Ingredient).filter(
                        Ingredient.name == ing_name_clean
                    ).first()

                    if not existing:
                        existing = Ingredient(
                            name=ing_name_clean,
                            irritation_level=get_irritation_level(ing_name_clean)
                        )
                        db.add(existing)
                        db.flush()
                        ingredients_added += 1

                    ingredient_cache[cache_key] = existing

                ingredient = ingredient_cache[cache_key]

                # ── 3. Link ingredient to concern (avoid duplicates) ──────
                if ingredient not in concern.recommended_ingredients:
                    concern.recommended_ingredients.append(ingredient)
                    links_added += 1

        db.commit()
        print(f"✅ Done!")
        print(f"   Concerns added:    {concerns_added}")
        print(f"   Ingredients added: {ingredients_added}")
        print(f"   Links created:     {links_added}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()