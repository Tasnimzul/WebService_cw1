
"""
tests/test_api.py
─────────────────
Comprehensive test suite for the Skincare & Ingredient Analysis API.
Run from project root: pytest tests/ -v
 
Uses FastAPI's TestClient (via httpx) with a separate in-memory SQLite
database so tests never touch the real skincare.db.
"""
 
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from app.main import app
from app.database import Base, get_db
 
# ── TEST DATABASE (in-memory SQLite, separate from dev db) ───────────────────
TEST_DATABASE_URL = "sqlite:///./test.db"
 
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
 
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 
app.dependency_overrides[get_db] = override_get_db
 
 
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before tests, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
 
 
@pytest.fixture(scope="session")
def client():
    return TestClient(app)
 
 
# ── HELPERS ───────────────────────────────────────────────────────────────────
 
def register_and_login(client, username="testuser", password="testpass123"):
    """Register a user and return their JWT token."""
    client.post("/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": password
    })
    res = client.post("/auth/login", data={"username": username, "password": password})
    return res.json()["access_token"]
 
 
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
 
 
def create_test_product(client, name="Test Serum", product_type="Serum", price=25.0):
    """Create a product and return its ID."""
    res = client.post("/products/", json={"name": name, "product_type": product_type, "price": price})
    return res.json()["id"]
 
 
# ═════════════════════════════════════════════════════════════════════════════
# AUTH TESTS
# ═════════════════════════════════════════════════════════════════════════════
 
class TestAuth:
 
    def test_register_success(self, client):
        res = client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "password123"
        })
        assert res.status_code == 201
        data = res.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@test.com"
        assert "id" in data
        assert "hashed_password" not in data  # password never exposed
 
    def test_register_duplicate_username(self, client):
        client.post("/auth/register", json={
            "username": "dupuser", "email": "dup1@test.com", "password": "pass123"
        })
        res = client.post("/auth/register", json={
            "username": "dupuser", "email": "dup2@test.com", "password": "pass123"
        })
        assert res.status_code == 400
        assert "Username already taken" in res.json()["detail"]
 
    def test_register_duplicate_email(self, client):
        client.post("/auth/register", json={
            "username": "emailuser1", "email": "same@test.com", "password": "pass123"
        })
        res = client.post("/auth/register", json={
            "username": "emailuser2", "email": "same@test.com", "password": "pass123"
        })
        assert res.status_code == 400
        assert "Email already registered" in res.json()["detail"]
 
    def test_login_success(self, client):
        client.post("/auth/register", json={
            "username": "loginuser", "email": "login@test.com", "password": "pass123"
        })
        res = client.post("/auth/login", data={"username": "loginuser", "password": "pass123"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
 
    def test_login_wrong_password(self, client):
        client.post("/auth/register", json={
            "username": "wrongpass", "email": "wrong@test.com", "password": "correct"
        })
        res = client.post("/auth/login", data={"username": "wrongpass", "password": "incorrect"})
        assert res.status_code == 401
 
    def test_login_nonexistent_user(self, client):
        res = client.post("/auth/login", data={"username": "nobody", "password": "pass"})
        assert res.status_code == 401
 
 
# ═════════════════════════════════════════════════════════════════════════════
# USER TESTS
# ═════════════════════════════════════════════════════════════════════════════
 
class TestUsers:
 
    def test_get_me(self, client):
        token = register_and_login(client, "getmeuser", "pass123")
        res = client.get("/users/me", headers=auth_headers(token))
        assert res.status_code == 200
        assert res.json()["username"] == "getmeuser"
 
    def test_get_me_unauthorized(self, client):
        res = client.get("/users/me")
        assert res.status_code == 401
 
    def test_update_me(self, client):
        token = register_and_login(client, "updateuser", "pass123")
        res = client.put("/users/me", json={"username": "updateduser"}, headers=auth_headers(token))
        assert res.status_code == 200
        assert res.json()["username"] == "updateduser"
 
    def test_delete_me(self, client):
        token = register_and_login(client, "deleteuser", "pass123")
        res = client.delete("/users/me", headers=auth_headers(token))
        assert res.status_code == 204
 
 
# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT TESTS
# ═════════════════════════════════════════════════════════════════════════════
 
class TestProducts:
 
    def test_get_products_empty(self, client):
        res = client.get("/products/")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
 
    def test_create_product(self, client):
        res = client.post("/products/", json={
            "name": "Hydrating Serum",
            "product_type": "Serum",
            "price": 29.99
        })
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Hydrating Serum"
        assert data["product_type"] == "Serum"
        assert data["price"] == 29.99
        assert "id" in data
 
    def test_create_product_minimal(self, client):
        """Product with only name — type and price optional."""
        res = client.post("/products/", json={"name": "Mystery Product"})
        assert res.status_code == 201
        assert res.json()["name"] == "Mystery Product"
 
    def test_get_product_by_id(self, client):
        product_id = create_test_product(client, "Get By ID Serum")
        res = client.get(f"/products/{product_id}")
        assert res.status_code == 200
        assert res.json()["id"] == product_id
 
    def test_get_product_not_found(self, client):
        res = client.get("/products/99999")
        assert res.status_code == 404
 
    def test_update_product(self, client):
        product_id = create_test_product(client, "Old Name")
        res = client.put(f"/products/{product_id}", json={"name": "New Name"})
        assert res.status_code == 200
        assert res.json()["name"] == "New Name"
 
    def test_update_product_price_only(self, client):
        """Updating price should not change name."""
        product_id = create_test_product(client, "Price Test Product", price=10.0)
        res = client.put(f"/products/{product_id}", json={"price": 99.99})
        assert res.status_code == 200
        data = res.json()
        assert data["price"] == 99.99
        assert data["name"] == "Price Test Product"  # name unchanged
 
    def test_update_product_not_found(self, client):
        res = client.put("/products/99999", json={"name": "Ghost"})
        assert res.status_code == 404
 
    def test_delete_product(self, client):
        product_id = create_test_product(client, "To Be Deleted")
        res = client.delete(f"/products/{product_id}")
        assert res.status_code == 204
        # verify it's gone
        res = client.get(f"/products/{product_id}")
        assert res.status_code == 404
 
    def test_filter_products_by_type(self, client):
        client.post("/products/", json={"name": "Filter Serum", "product_type": "Serum", "price": 20.0})
        res = client.get("/products/?product_type=Serum")
        assert res.status_code == 200
        results = res.json()
        assert all(p["product_type"] == "Serum" for p in results)
 
    def test_filter_products_by_price(self, client):
        client.post("/products/", json={"name": "Cheap Product", "product_type": "Toner", "price": 5.0})
        client.post("/products/", json={"name": "Expensive Product", "product_type": "Toner", "price": 100.0})
        res = client.get("/products/?max_price=10")
        assert res.status_code == 200
        results = res.json()
        assert all(p["price"] <= 10 for p in results if p["price"] is not None)
 
 
# ═════════════════════════════════════════════════════════════════════════════
# SAFETY SCORE TESTS
# ═════════════════════════════════════════════════════════════════════════════
 
class TestSafetyScore:
 
    def test_safety_score_no_ingredients(self, client):
        """Product with no ingredients should return 404."""
        product_id = create_test_product(client, "Empty Product")
        res = client.get(f"/products/{product_id}/safety-score")
        assert res.status_code == 404
 
    def test_safety_score_not_found(self, client):
        res = client.get("/products/99999/safety-score")
        assert res.status_code == 404
 
    def test_safety_score_structure(self, client):
        """Safety score response has all required fields."""
        # create product with ingredients
        from app.models.models import Ingredient, ProductIngredient, Product
        from app.database import SessionLocal
 
        db = TestingSessionLocal()
        # add a product with a known ingredient
        ing = Ingredient(name="test glycerin", irritation_level="low")
        db.add(ing)
        db.flush()
        product = Product(name="Safety Test Product", product_type="Serum", price=15.0)
        db.add(product)
        db.flush()
        link = ProductIngredient(product_id=product.id, ingredient_id=ing.id, position=1)
        db.add(link)
        db.commit()
        product_id = product.id
        db.close()
 
        res = client.get(f"/products/{product_id}/safety-score")
        assert res.status_code == 200
        data = res.json()
        assert "safety_score" in data
        assert "total_ingredients" in data
        assert "high_irritation_count" in data
        assert "medium_irritation_count" in data
        assert "low_irritation_count" in data
        assert 0 <= data["safety_score"] <= 10
 
 
# ═════════════════════════════════════════════════════════════════════════════
# CONFLICT CHECK TESTS
# ═════════════════════════════════════════════════════════════════════════════
 
class TestConflicts:
 
    def test_conflict_check_needs_two_products(self, client):
        res = client.post("/products/conflict-check", json={"product_ids": [1]})
        assert res.status_code == 400
 
    def test_conflict_check_no_conflicts(self, client):
        p1 = create_test_product(client, "Conflict Test P1")
        p2 = create_test_product(client, "Conflict Test P2")
        res = client.post("/products/conflict-check", json={"product_ids": [p1, p2]})
        assert res.status_code == 200
        data = res.json()
        assert "has_conflicts" in data
        assert "conflicts" in data
        assert isinstance(data["conflicts"], list)
 
    def test_get_all_conflicts(self, client):
        res = client.get("/conflicts/")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
 
 
# ═════════════════════════════════════════════════════════════════════════════
# PROFILE TESTS
# ═════════════════════════════════════════════════════════════════════════════
 
class TestProfile:
 
    def test_get_profile_unauthorized(self, client):
        res = client.get("/profile/")
        assert res.status_code == 401
 
    def test_get_profile_not_found(self, client):
        token = register_and_login(client, "noprofileuser", "pass123")
        res = client.get("/profile/", headers=auth_headers(token))
        assert res.status_code == 404
 
    def test_create_profile(self, client):
        token = register_and_login(client, "profileuser", "pass123")
        res = client.post("/profile/", json={"skin_type": "Oily"}, headers=auth_headers(token))
        assert res.status_code == 201
        data = res.json()
        assert data["skin_type"] == "Oily"
        assert "concerns" in data
 
    def test_create_profile_duplicate(self, client):
        token = register_and_login(client, "dupprofile", "pass123")
        client.post("/profile/", json={"skin_type": "Dry"}, headers=auth_headers(token))
        res = client.post("/profile/", json={"skin_type": "Oily"}, headers=auth_headers(token))
        assert res.status_code == 400
 
    def test_get_profile(self, client):
        token = register_and_login(client, "getprofile", "pass123")
        client.post("/profile/", json={"skin_type": "Normal"}, headers=auth_headers(token))
        res = client.get("/profile/", headers=auth_headers(token))
        assert res.status_code == 200
        assert res.json()["skin_type"] == "Normal"
 
    def test_update_profile(self, client):
        token = register_and_login(client, "updateprofile", "pass123")
        client.post("/profile/", json={"skin_type": "Dry"}, headers=auth_headers(token))
        res = client.put("/profile/", json={"skin_type": "Oily"}, headers=auth_headers(token))
        assert res.status_code == 200
        assert res.json()["skin_type"] == "Oily"
 
    def test_delete_profile(self, client):
        token = register_and_login(client, "deleteprofile", "pass123")
        client.post("/profile/", json={"skin_type": "Combination"}, headers=auth_headers(token))
        res = client.delete("/profile/", headers=auth_headers(token))
        assert res.status_code == 204
        # verify it's gone
        res = client.get("/profile/", headers=auth_headers(token))
        assert res.status_code == 404
 
    def test_recommendations_no_concerns(self, client):
        token = register_and_login(client, "recuser", "pass123")
        client.post("/profile/", json={"skin_type": "Oily"}, headers=auth_headers(token))
        res = client.get("/profile/recommendations", headers=auth_headers(token))
        assert res.status_code == 400  # no concerns set
 
    def test_recommendations_unauthorized(self, client):
        res = client.get("/profile/recommendations")
        assert res.status_code == 401
 
    def test_common_concerns_valid_skin_type(self, client):
        token = register_and_login(client, "concernsuser", "pass123")
        res = client.get("/profile/common-concerns?skin_type=Oily", headers=auth_headers(token))
        assert res.status_code in [200, 404]  # 404 if no concerns in test db
 
    def test_common_concerns_invalid_skin_type(self, client):
        token = register_and_login(client, "invalidconcern", "pass123")
        res = client.get("/profile/common-concerns?skin_type=Alien", headers=auth_headers(token))
        assert res.status_code == 422  # invalid enum value
 
 
# ═════════════════════════════════════════════════════════════════════════════
# ANALYTICS TESTS
# ═════════════════════════════════════════════════════════════════════════════
 
class TestAnalytics:
 
    def test_concern_distribution_empty(self, client):
        res = client.get("/analytics/concern-distribution")
        assert res.status_code == 200
        data = res.json()
        assert "total_profiles" in data
        assert "distribution" in data
        assert isinstance(data["distribution"], list)
 
    def test_ingredient_frequency_empty(self, client):
        res = client.get("/analytics/ingredient-frequency")
        assert res.status_code == 200
        data = res.json()
        assert "total_products" in data
        assert "top_ingredients" in data
        assert isinstance(data["top_ingredients"], list)
 
    def test_ingredient_frequency_structure(self, client):
        """If products exist, frequency items have correct fields."""
        res = client.get("/analytics/ingredient-frequency")
        assert res.status_code == 200
        data = res.json()
        if data["top_ingredients"]:
            item = data["top_ingredients"][0]
            assert "name" in item
            assert "appears_in" in item
            assert "percentage" in item
 
 
# ═════════════════════════════════════════════════════════════════════════════
# PROFILE MATCH TESTS
# ═════════════════════════════════════════════════════════════════════════════
 
class TestProfileMatch:
 
    def test_profile_match_valid(self, client):
        product_id = create_test_product(client, "Match Test Product")
        res = client.get(f"/products/{product_id}/profile-match?skin_type=Oily")
        assert res.status_code == 200
        data = res.json()
        assert "match_score" in data
        assert "matching_ingredients" in data
        assert 0 <= data["match_score"] <= 100
 
    def test_profile_match_not_found(self, client):
        res = client.get("/products/99999/profile-match?skin_type=Oily")
        assert res.status_code == 404
 
    def test_profile_match_invalid_skin_type(self, client):
        product_id = create_test_product(client, "Invalid Skin Type Product")
        res = client.get(f"/products/{product_id}/profile-match?skin_type=Alien")
        assert res.status_code == 422
 
 
# ═════════════════════════════════════════════════════════════════════════════
# ROOT + GENERAL TESTS
# ═════════════════════════════════════════════════════════════════════════════
 
class TestGeneral:
 
    def test_root_returns_frontend(self, client):
        res = client.get("/")
        assert res.status_code == 200
 
    def test_invalid_token(self, client):
        res = client.get("/profile/", headers={"Authorization": "Bearer invalidtoken"})
        assert res.status_code == 401
 
    def test_missing_token(self, client):
        res = client.get("/profile/")
        assert res.status_code == 401
 