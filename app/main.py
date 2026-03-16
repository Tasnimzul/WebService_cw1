from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.models import models
from app.routers import products, auth, profile, analytics, conflicts, users

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Skincare & Ingredient Analysis API",
    description="A skincare product recommendation and ingredient analysis API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(profile.router)
app.include_router(analytics.router)
app.include_router(conflicts.router)
app.include_router(users.router)

@app.get("/")
def root():
    return FileResponse("frontend/index.html")