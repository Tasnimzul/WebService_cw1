from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import SkinConcern, SkinProfile, ProductIngredient, Ingredient, profile_concern
from app.schemas.schemas import ConcernDistributionResponse, ConcernDistributionItem, IngredientFrequencyResponse, IngredientFrequencyItem

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/concern-distribution", response_model=ConcernDistributionResponse)
def concern_distribution(db: Session = Depends(get_db)):
    total_profiles = db.query(SkinProfile).count()

    if total_profiles == 0:
        return ConcernDistributionResponse(
            total_profiles=0,
            most_common="N/A",
            distribution=[]
        )

    # count how many profiles have each concern
    results = db.query(
        SkinConcern.name,
        SkinConcern.skin_type,
        func.count(profile_concern.c.profile_id).label('count')
    ).join(
        profile_concern,
        SkinConcern.id == profile_concern.c.concern_id
    ).group_by(
        SkinConcern.name,
        SkinConcern.skin_type
    ).order_by(
        func.count(profile_concern.c.profile_id).desc()
    ).all()

    distribution = [
        ConcernDistributionItem(
            concern=row.name,
            skin_type=row.skin_type,
            count=row.count,
            percentage=f"{round(row.count / total_profiles * 100, 1)}%"
        )
        for row in results
    ]

    most_common = distribution[0].concern if distribution else "N/A"

    return ConcernDistributionResponse(
        total_profiles=total_profiles,
        most_common=most_common,
        distribution=distribution
    )


@router.get("/ingredient-frequency", response_model=IngredientFrequencyResponse)
def ingredient_frequency(db: Session = Depends(get_db)):
    from app.models.models import Product

    total_products = db.query(Product).count()

    if total_products == 0:
        return IngredientFrequencyResponse(
            total_products=0,
            top_ingredients=[]
        )

    # count how many products each ingredient appears in
    results = db.query(
        Ingredient.name,
        func.count(ProductIngredient.product_id).label('count')
    ).join(
        ProductIngredient,
        Ingredient.id == ProductIngredient.ingredient_id
    ).group_by(
        Ingredient.name
    ).order_by(
        func.count(ProductIngredient.product_id).desc()
    ).limit(20).all()
    # top 20 most common ingredients

    top_ingredients = [
        IngredientFrequencyItem(
            name=row.name,
            appears_in=row.count,
            percentage=f"{round(row.count / total_products * 100, 1)}%"
        )
        for row in results
    ]

    return IngredientFrequencyResponse(
        total_products=total_products,
        top_ingredients=top_ingredients
    )