from fastapi import FastAPI
from app.database import engine, Base
from app.models import models
from app.routers import products, auth, profile, analytics, conflicts

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Skincare & Ingredient Analysis API",
    description="A skincare product recommendation and ingredient analysis API",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(profile.router)
app.include_router(analytics.router)
app.include_router(conflicts.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to the Skincare API",
        "docs": "Visit /docs for Swagger UI",
        "version": "1.0.0"
    }