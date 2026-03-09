from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import IngredientConflict
from app.schemas.schemas import IngredientConflictResponse

router = APIRouter(prefix="/conflicts", tags=["Ingredient Conflicts"])


@router.get("/", response_model=List[IngredientConflictResponse])
def get_conflicts(db: Session = Depends(get_db)):
    return db.query(IngredientConflict).all()