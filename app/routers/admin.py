from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import User, Ingredient, IngredientConflict
from app.schemas.schemas import (
    UserResponse,
    IngredientConflictCreate, IngredientConflictResponse
)
from app.core.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])
#Every single endpoint in this router requires admin: User = Depends(get_current_admin). 
# Remember from core/auth.py — get_current_admin chains on top of get_current_user, so it first validates the JWT and then additionally checks is_admin=True. 
# Any non-admin gets a 403 Forbidden.


#USERS

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(User).all()


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot delete another admin")
    db.delete(user)
    db.commit()


@router.put("/users/{user_id}/make-admin", response_model=UserResponse)
def make_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = True
    #Notice there's no make-admin=False endpoint — once admin, always admin unless manually changed in the database.
    db.commit()
    db.refresh(user)
    return user



#Conflicts

@router.post("/conflicts", response_model=IngredientConflictResponse, status_code=201)
def create_conflict(
    conflict: IngredientConflictCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    if conflict.severity not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="severity must be low, medium, or high")
    # validate both ingredients exist
    ing_1 = db.query(Ingredient).filter(Ingredient.id == conflict.ingredient_1_id).first()
    ing_2 = db.query(Ingredient).filter(Ingredient.id == conflict.ingredient_2_id).first()
    if not ing_1:
        raise HTTPException(status_code=404, detail=f"Ingredient ID {conflict.ingredient_1_id} not found")
    if not ing_2:
        raise HTTPException(status_code=404, detail=f"Ingredient ID {conflict.ingredient_2_id} not found")

    # always store lower ID first
    id_a = min(conflict.ingredient_1_id, conflict.ingredient_2_id)
    id_b = max(conflict.ingredient_1_id, conflict.ingredient_2_id)

    if id_a == id_b:
        raise HTTPException(status_code=400, detail="Cannot create conflict between same ingredient")

    existing = db.query(IngredientConflict).filter(
        IngredientConflict.ingredient_1_id == id_a,
        IngredientConflict.ingredient_2_id == id_b
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Conflict pair already exists")

    db_conflict = IngredientConflict(
        ingredient_1_id=id_a,
        ingredient_2_id=id_b,
        severity=conflict.severity
    )
    db.add(db_conflict)
    db.commit()
    db.refresh(db_conflict)
    return db_conflict


@router.delete("/conflicts/{conflict_id}", status_code=204)
def delete_conflict(
    conflict_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    conflict = db.query(IngredientConflict).filter(
        IngredientConflict.id == conflict_id
    ).first()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    db.delete(conflict)
    db.commit()