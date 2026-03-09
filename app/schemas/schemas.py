from pydantic import BaseModel, EmailStr
from typing import Optional, List


# ─────────────────────────────────────────
# INGREDIENT
# ─────────────────────────────────────────

class IngredientBase(BaseModel):
    name: str

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(BaseModel):
    irritation_level: str  # low / medium / high

class IngredientResponse(IngredientBase):
    id: int
    irritation_level: str

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# SKIN CONCERN
# ─────────────────────────────────────────

class SkinConcernBase(BaseModel):
    name: str #the name of skin concern itself
    skin_type: str

class SkinConcernCreate(SkinConcernBase):
    pass

class SkinConcernResponse(SkinConcernBase):
    id: int
    recommended_ingredients: List[IngredientResponse] = []

    class Config: #take from db
        from_attributes = True


# ─────────────────────────────────────────
# PRODUCT
# ─────────────────────────────────────────

class ProductBase(BaseModel):
    name: str
    product_type: Optional[str] = None
    price: Optional[float] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    product_type: Optional[str] = None
    price: Optional[float] = None

class ProductIngredientResponse(BaseModel):
#This is never used directly by an endpoint. It's nested inside ProductResponse. Represents one row from product_ingredients bridge table:
    position: int
    ingredient: IngredientResponse

    class Config:
        from_attributes = True

class ProductResponse(ProductBase):
    id: int
    product_ingredients: List[ProductIngredientResponse] = []

    class Config:
        from_attributes = True

class ProductSummaryResponse(ProductBase): #basically response with no ingredients
    id: int

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# INGREDIENT CONFLICT
# ─────────────────────────────────────────

class IngredientConflictBase(BaseModel):
    ingredient_1_id: int
    ingredient_2_id: int
    severity: str

class IngredientConflictCreate(IngredientConflictBase): #only used by admin
    pass

class IngredientConflictResponse(IngredientConflictBase):
    id: int
    ingredient_1: IngredientResponse
    ingredient_2: IngredientResponse

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel): #used when returning token after succesful login. User stores this token and send it with every protected request
    access_token: str
    token_type: str = "bearer"


# ─────────────────────────────────────────
# SKIN PROFILE
# ─────────────────────────────────────────

class SkinProfileCreate(BaseModel):
    skin_type: str                          # required
    concern_ids: Optional[List[int]] = None # optional

class SkinProfileUpdate(BaseModel):
    skin_type: Optional[str] = None
    concern_ids: Optional[List[int]] = None

class SkinProfileResponse(BaseModel): #returns full profile with their recommended ingredients
    id: int
    skin_type: str
    concerns: List[SkinConcernResponse] = []

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────

class SafetyScoreResponse(BaseModel):
    product_id: int
    product_name: str
    safety_score: float
    total_ingredients: int
    high_irritation_count: int
    medium_irritation_count: int
    low_irritation_count: int


class RecommendationResponse(BaseModel): #recommend products
    skin_type: str
    concerns: List[str] = []
    recommended_ingredients: List[IngredientResponse] = []
    matching_products: List[ProductSummaryResponse] = []
    total_found: int

class ConcernDistributionItem(BaseModel):
    concern: str
    skin_type: str
    count: int
    percentage: str

class ConcernDistributionResponse(BaseModel):
    total_profiles: int
    most_common: str
    distribution: List[ConcernDistributionItem] = []

class IngredientFrequencyItem(BaseModel):
    name: str
    appears_in: int
    percentage: str

class IngredientFrequencyResponse(BaseModel):
    total_products: int
    top_ingredients: List[IngredientFrequencyItem] = []

class ProfileMatchResponse(BaseModel):
    product_id: int
    product_name: str
    skin_type: str
    match_score: float
    matching_ingredients: List[str] = []
    total_recommended: int
    matched: int

class ProductConflictCheckRequest(BaseModel):
    product_ids: List[int]

class ProductConflictItem(BaseModel):
    product_1: str
    product_2: str
    conflicting_ingredients: str
    severity: str

class ProductConflictCheckResponse(BaseModel):
    products_checked: List[ProductSummaryResponse] = []
    has_conflicts: bool
    conflict_count: int
    conflicts: List[ProductConflictItem] = []