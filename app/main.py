from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.models import models
from app.routers import products, auth, profile, analytics, conflicts, users, admin, ingredients

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

Base.metadata.create_all(bind=engine)
import subprocess
subprocess.run(["python", "data/import_concerns.py"])
subprocess.run(["python", "data/import_products.py"])
subprocess.run(["python", "data/import_conflicts.py"])
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Skincare & Ingredient Analysis API",
    description="A skincare product recommendation and ingredient analysis API",
    version="1.0.0",
    openapi_tags=[
        {"name": "Auth", "description": "Register and login"},
        {"name": "Users", "description": "Manage your account"},
        {"name": "Admin", "description": "Admin-only user and conflict management"},
        {"name": "Products", "description": "Browse and manage skincare products"},
        {"name": "Skin Profile", "description": "Create and manage your skin profile"},
        {"name": "Analytics", "description": "Product and ingredient analytics, conflict checking, and recommendations"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(products.router_analytics)
app.include_router(profile.router)
app.include_router(profile.router_analytics)
app.include_router(analytics.router)
app.include_router(conflicts.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(ingredients.router)

@app.get("/")
def root():
    return FileResponse("frontend/index.html")