from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Ingredient
from app.schemas.schemas import IngredientResponse

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])

@router.get("/", response_model=List[IngredientResponse])
def get_ingredients(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Ingredient)
    if search:
        query = query.filter(Ingredient.name.ilike(f"%{search}%"))
    return query.limit(50).all()