from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import SkinConcern
from app.schemas.schemas import SkinConcernCreate, SkinConcernResponse

router = APIRouter(prefix="/concerns", tags=["Skin Concerns"])


@router.get("/", response_model=List[SkinConcernResponse])
def get_concerns(
    skin_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(SkinConcern)
    if skin_type:
        query = query.filter(SkinConcern.skin_type.ilike(f"%{skin_type}%"))
    return query.all()


@router.get("/{concern_id}", response_model=SkinConcernResponse)
def get_concern(concern_id: int, db: Session = Depends(get_db)):
    concern = db.query(SkinConcern).filter(SkinConcern.id == concern_id).first()
    if not concern:
        raise HTTPException(status_code=404, detail="Concern not found")
    return concern


@router.post("/", response_model=SkinConcernResponse, status_code=201)
def create_concern(concern: SkinConcernCreate, db: Session = Depends(get_db)):
    db_concern = SkinConcern(
        name=concern.name,
        skin_type=concern.skin_type
    )
    db.add(db_concern)
    db.commit()
    db.refresh(db_concern)
    return db_concern


@router.delete("/{concern_id}", status_code=204)
def delete_concern(concern_id: int, db: Session = Depends(get_db)):
    concern = db.query(SkinConcern).filter(SkinConcern.id == concern_id).first()
    if not concern:
        raise HTTPException(status_code=404, detail="Concern not found")
    db.delete(concern)
    db.commit()