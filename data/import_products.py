"""
import_products.py
──────────────────
Imports products + ingredients from the Lookfantastic dataset.
Run from project root: python data/import_products.py

What this does:
  1. Reads skincare_products_clean.csv
  2. For each row → creates a Product row
  3. Parses the clean_ingreds column (Python list string) → creates Ingredient rows
  4. Links ingredients to products via ProductIngredient (with position = concentration order)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ast
import re
import pandas as pd
from app.database import SessionLocal, engine, Base
from app.models.models import Product, Ingredient, ProductIngredient

# ── irritation level lookup (same as import_concerns.py) ────────────────────
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

    # Low irritation
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
    name_lower = ingredient_name.lower().strip()
    for key, level in IRRITATION_LOOKUP.items():
        if key in name_lower:
            return level
    return "low"


def parse_price(price_str) -> float | None:
    """Convert '£13.00' → 13.0. Returns None if unparseable."""
    if pd.isna(price_str):
        return None
    try:
        cleaned = re.sub(r"[^\d.]", "", str(price_str))
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def parse_ingredients(raw: str) -> list[str]:
    """
    Parse the clean_ingreds column.
    Format is a Python list string: "['glycerin', 'niacinamide', ...]"
    Returns a list of ingredient name strings.
    """
    if pd.isna(raw):
        return []
    try:
        result = ast.literal_eval(str(raw))
        if isinstance(result, list):
            return [str(i).strip() for i in result if str(i).strip()]
    except (ValueError, SyntaxError):
        pass
    return []


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        df = pd.read_csv("data/skincare_products_clean.csv")
        print(f"Loaded {len(df)} rows from Lookfantastic dataset")

        products_added = 0
        ingredients_added = 0
        links_added = 0

        # Cache ingredients already seen this run to avoid redundant DB hits
        ingredient_cache: dict[str, Ingredient] = {}

        for _, row in df.iterrows():
            name = str(row["product_name"]).strip()
            product_type = str(row["product_type"]).strip() if not pd.isna(row["product_type"]) else None
            price = parse_price(row["price"])
            ingredient_names = parse_ingredients(row["clean_ingreds"])

            # ── 1. Create Product ─────────────────────────────────────────
            product = Product(
                name=name,
                product_type=product_type,
                price=price
            )
            db.add(product)
            db.flush()  # get product.id
            products_added += 1

            # ── 2. Create ingredients + ProductIngredient links ───────────
            for position, ing_name in enumerate(ingredient_names, start=1):
                # position 1 = highest concentration (first in list)
                cache_key = ing_name.lower()

                if cache_key not in ingredient_cache:
                    existing = db.query(Ingredient).filter(
                        Ingredient.name == ing_name
                    ).first()

                    if not existing:
                        existing = Ingredient(
                            name=ing_name,
                            irritation_level=get_irritation_level(ing_name)
                        )
                        db.add(existing)
                        db.flush()
                        ingredients_added += 1

                    ingredient_cache[cache_key] = existing

                ingredient = ingredient_cache[cache_key]

                link = ProductIngredient(
                    product_id=product.id,
                    ingredient_id=ingredient.id,
                    position=position
                )
                db.add(link)
                links_added += 1

            # Commit in batches of 100 for performance
            if products_added % 100 == 0:
                db.commit()
                print(f"   ...{products_added} products imported")

        db.commit()
        print(f"Done!")
        print(f"   Products added:    {products_added}")
        print(f"   Ingredients added: {ingredients_added}")
        print(f"   Links created:     {links_added}")

    except Exception as e:
        db.rollback()
        print(f" Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()