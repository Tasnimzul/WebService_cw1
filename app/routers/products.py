from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from itertools import combinations
from app.database import get_db
from app.models.models import Product, ProductIngredient, Ingredient, IngredientConflict, SkinConcern
from app.schemas.schemas import (
    ProductCreate, ProductUpdate,
    ProductResponse, ProductSummaryResponse,
    SafetyScoreResponse, ProfileMatchResponse,
    ProductConflictCheckRequest, ProductConflictCheckResponse, ProductConflictItem
)
from rapidfuzz import fuzz
from app.schemas.schemas import SkinTypeEnum, ProductTypeEnum

router = APIRouter(prefix="/products", tags=["Products"])

def is_ingredient_match(product_ing: str, recommended_set: set) -> bool:
    p = product_ing.lower().strip()
    for r in recommended_set:
        if r in p or p in r:
            return True
        if len(p) <= len(r) * 2 and len(r) <= len(p) * 2:
            if fuzz.ratio(p, r) >= 80:
                return True
    return False


# ─────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────

@router.get("/", response_model=List[ProductSummaryResponse])
def get_products(
    product_type: Optional[ProductTypeEnum] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if product_type:
        query = query.filter(Product.product_type == product_type.value)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    return query.all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(
        name=product.name,
        product_type=product.product_type,
        price=product.price
    )
    db.add(db_product)
    db.flush()

    if product.ingredient_ids:
        # validate all ingredient IDs exist
        ingredients = db.query(Ingredient).filter(
            Ingredient.id.in_(product.ingredient_ids)
        ).all()

        found_ids = {i.id for i in ingredients}
        missing = [i for i in product.ingredient_ids if i not in found_ids]
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Ingredient IDs not found: {missing}"
            )

        # position = order they were provided (1 = highest concentration)
        for position, ingredient_id in enumerate(product.ingredient_ids, start=1):
            link = ProductIngredient(
                product_id=db_product.id,
                ingredient_id=ingredient_id,
                position=position
            )
            db.add(link)

    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product_update.name is not None:
        product.name = product_update.name
    if product_update.product_type is not None:
        product.product_type = product_update.product_type
    if product_update.price is not None:
        product.price = product_update.price
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()


# ─────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────

@router.get("/{product_id}/safety-score", response_model=SafetyScoreResponse)
def get_safety_score(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    ingredients = [pi.ingredient for pi in product.product_ingredients]
    if not ingredients:
        raise HTTPException(status_code=404, detail="No ingredients found for this product")

    high = sum(1 for i in ingredients if i.irritation_level == 'high')
    medium = sum(1 for i in ingredients if i.irritation_level == 'medium')
    low = sum(1 for i in ingredients if i.irritation_level == 'low')
    total = len(ingredients)

    score = 10 - ((high * 2) + (medium * 0.5)) / total * 10
    score = round(max(0, min(10, score)), 1)

    return SafetyScoreResponse(
        product_id=product.id,
        product_name=product.name,
        safety_score=score,
        total_ingredients=total,
        high_irritation_count=high,
        medium_irritation_count=medium,
        low_irritation_count=low
    )


@router.post("/conflict-check", response_model=ProductConflictCheckResponse)
def check_product_conflicts(
    request: ProductConflictCheckRequest,
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(
        Product.id.in_(request.product_ids)
    ).all()

    if len(products) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least 2 product IDs"
        )

    # get ingredient ids per product
    product_ingredients = {}
    for product in products:
        product_ingredients[product.id] = {
            pi.ingredient_id for pi in product.product_ingredients
        }

    # check every pair of products
    found_conflicts = []
    for product_a, product_b in combinations(products, 2):
        ids_a = product_ingredients[product_a.id]
        ids_b = product_ingredients[product_b.id]

        conflicts = db.query(IngredientConflict).filter(
            (
                IngredientConflict.ingredient_1_id.in_(ids_a) &
                IngredientConflict.ingredient_2_id.in_(ids_b)
            ) |
            (
                IngredientConflict.ingredient_1_id.in_(ids_b) &
                IngredientConflict.ingredient_2_id.in_(ids_a)
            )
        ).all()

        for conflict in conflicts:
            found_conflicts.append(ProductConflictItem(
                product_1=product_a.name,
                product_2=product_b.name,
                conflicting_ingredients=f"{conflict.ingredient_1.name} + {conflict.ingredient_2.name}",
                severity=conflict.severity
            ))

    return ProductConflictCheckResponse(
        products_checked=products,
        has_conflicts=len(found_conflicts) > 0,
        conflict_count=len(found_conflicts),
        conflicts=found_conflicts
    )


@router.get("/{product_id}/profile-match", response_model=ProfileMatchResponse)
def profile_match(
    product_id: int,
    skin_type: SkinTypeEnum = Query(...),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    concerns = db.query(SkinConcern).filter(
        SkinConcern.skin_type.ilike(skin_type)
    ).all()

    recommended_names = set()
    for concern in concerns:
        for ingredient in concern.recommended_ingredients:
            recommended_names.add(ingredient.name.lower())

    product_ingredient_names = [
        pi.ingredient.name for pi in product.product_ingredients
    ]

    matches = [
        name for name in product_ingredient_names
        if is_ingredient_match(name, recommended_names)
    ]

    total_recommended = len(recommended_names)
    matched = len(matches)
    score = round((matched / total_recommended * 100), 1) if total_recommended > 0 else 0.0

    return ProfileMatchResponse(
        product_id=product.id,
        product_name=product.name,
        skin_type=skin_type,
        match_score=score,
        matching_ingredients=matches,
        total_recommended=total_recommended,
        matched=matched
    )