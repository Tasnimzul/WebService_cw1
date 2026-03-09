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

router = APIRouter(prefix="/profile", tags=["Skin Profile"])


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

    # get recommended ingredients from all user concerns
    recommended_ingredients = []
    seen_ids = set()
    for concern in profile.concerns:
        for ingredient in concern.recommended_ingredients:
            if ingredient.id not in seen_ids:
                recommended_ingredients.append(ingredient)
                seen_ids.add(ingredient.id)

    # find products containing any of those ingredients
    recommended_ingredient_ids = [i.id for i in recommended_ingredients]

    product_ids = db.query(ProductIngredient.product_id).filter(
        ProductIngredient.ingredient_id.in_(recommended_ingredient_ids)
    ).distinct().all()

    product_ids = [p[0] for p in product_ids]

    from app.models.models import Product
    matching_products = db.query(Product).filter(
        Product.id.in_(product_ids)
    ).all()

    return RecommendationResponse(
        skin_type=profile.skin_type,
        concerns=[c.name for c in profile.concerns],
        recommended_ingredients=recommended_ingredients,
        matching_products=matching_products,
        total_found=len(matching_products)
    )