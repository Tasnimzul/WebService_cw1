from fastapi import FastAPI
from app.database import engine, Base
from app.models import models  # this line makes sure tables are created

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Skincare & Ingredient Analysis API", 
    description="An API for analysing skincare products, \
    ingredients, safety scores and personalised recommendations",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "Welcome to the Skincare API",
        "docs": "Visit /docs for Swagger UI",
        "version": "1.0.0"
    }