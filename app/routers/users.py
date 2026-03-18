from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import UserResponse, UserUpdate
from app.core.auth import get_current_user
from app.core.security import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
#it validates the JWT, fetches the user from the database, and passes them in. The function itself just returns that user object directly.


@router.put("/me", response_model=UserResponse)
def update_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_update.username is not None:
        existing = db.query(User).filter(
            User.username == user_update.username,
            User.id != current_user.id #The uniqueness check filters out the current user — User.id != current_user.id — so you can submit your own current username without getting a "already taken" error.
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = user_update.username

    if user_update.email is not None:
        existing = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = user_update.email

    if user_update.new_password is not None:
        if not user_update.current_password:
            raise HTTPException(status_code=400, detail="Current password required to set a new password")
        if not verify_password(user_update.current_password, current_user.hashed_password):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        current_user.hashed_password = hash_password(user_update.new_password)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=204)
def delete_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.delete(current_user)
    db.commit()