from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import SkinProfile, SkinConcern, Ingredient, ProductIngredient
from app.schemas.schemas import (
    SkinProfileCreate, SkinProfileUpdate,
    SkinProfileResponse, RecommendationResponse
)
from app.core.auth import get_current_user
from app.models.models import User
from rapidfuzz import fuzz

router = APIRouter(prefix="/profile", tags=["Skin Profile"])


def is_ingredient_match(product_ing: str, recommended_set: set) -> bool: #uses combination of fuzzy and if contains matching
    """
    Match product ingredient against recommended ingredients using:
    1. Contains check — handles long compound names e.g. 'tea tree gluconic acid' vs 'gluconic acid'
    2. Fuzzy match — handles typos e.g. 'salysilic acid' vs 'salicylic acid'
       Only applied to similar-length strings to avoid false positives.
    """
    p = product_ing.lower().strip()
    for r in recommended_set:
        if r in p or p in r:
            return True
        if len(p) <= len(r) * 2 and len(r) <= len(p) * 2:
            if fuzz.ratio(p, r) >= 80:
                return True
    return False


@router.post("/", response_model=SkinProfileResponse, status_code=201)
def create_profile(
    profile: SkinProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # check user doesn't already have a profile
    if current_user.profile:
        raise HTTPException(status_code=400, detail="Profile already exists. Use PUT to update.")

    db_profile = SkinProfile(
        user_id=current_user.id,
        skin_type=profile.skin_type
    )

    # link concerns if provided
    if profile.concern_ids:
        concerns = db.query(SkinConcern).filter(
            SkinConcern.id.in_(profile.concern_ids)
        ).all()
        db_profile.concerns = concerns

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


@router.get("/", response_model=SkinProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.profile:
        raise HTTPException(status_code=404, detail="No profile found. Use POST to create one.")
    return current_user.profile


@router.put("/", response_model=SkinProfileResponse)
def update_profile(
    profile_update: SkinProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="No profile found. Use POST to create one.")

    if profile_update.skin_type is not None:
        profile.skin_type = profile_update.skin_type

    if profile_update.concern_ids is not None:
        concerns = db.query(SkinConcern).filter(
            SkinConcern.id.in_(profile_update.concern_ids)
        ).all()
        profile.concerns = concerns

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/", status_code=204)
def delete_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="No profile found.")
    db.delete(profile)
    db.commit()


@router.get("/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="No profile found. Create a profile first.")

    if not profile.concerns:
        raise HTTPException(status_code=400, detail="No concerns in profile. Update your profile with concerns first.")

    # get recommended ingredient names from all user concerns
    recommended_names = set()
    recommended_ingredients = []
    seen_ids = set()
    for concern in profile.concerns:
        for ingredient in concern.recommended_ingredients:
            recommended_names.add(ingredient.name.lower().strip())
            if ingredient.id not in seen_ids:
                recommended_ingredients.append(ingredient)
                seen_ids.add(ingredient.id)

    # get all products and filter by fuzzy ingredient match
    from app.models.models import Product
    all_products = db.query(Product).all()

    matching_products = []
    for product in all_products:
        product_ingredient_names = [
            pi.ingredient.name for pi in product.product_ingredients
        ]
        if any(is_ingredient_match(name, recommended_names) for name in product_ingredient_names):
            matching_products.append(product)

    return RecommendationResponse(
        skin_type=profile.skin_type,
        concerns=[c.name for c in profile.concerns],
        recommended_ingredients=recommended_ingredients,
        matching_products=matching_products,
        total_found=len(matching_products)
    )