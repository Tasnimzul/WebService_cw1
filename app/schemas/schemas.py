from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum
# how data moves in and out of your API — what the user sends, and what they get back.

class SkinTypeEnum(str, Enum):
    normal = "Normal"
    dry = "Dry"
    oily = "Oily"
    combination = "Combination"

class ProductTypeEnum(str, Enum):
    moisturiser = "Moisturiser"
    serum = "Serum"
    oil = "Oil"
    mist = "Mist"
    balm = "Balm"
    mask = "Mask"
    peel = "Peel"
    eye_care = "Eye Care"
    cleanser = "Cleanser"
    toner = "Toner"
    exfoliator = "Exfoliator"
    bath_salts = "Bath Salts"
    body_wash = "Body Wash"
    bath_oil = "Bath Oil"


# INGREDIENT

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


# SKIN CONCERN


class SkinConcernBase(BaseModel):
    name: str
    skin_type: SkinTypeEnum

class SkinConcernCreate(SkinConcernBase):
    pass

class SkinConcernResponse(BaseModel):
    id: int
    name: str
    recommended_ingredients: List[IngredientResponse] = []

    class Config:
        from_attributes = True


# PRODUCT

class ProductBase(BaseModel):
    name: str
    product_type: Optional[ProductTypeEnum] = None
    price: Optional[float] = None

class ProductCreate(ProductBase):
    ingredient_ids: Optional[List[int]] = None # add ingredients from list when creating products

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Leave out to keep unchanged")
    product_type: Optional[ProductTypeEnum] = Field(None, description="Leave out to keep unchanged")
    price: Optional[float] = Field(None, description="Leave out to keep unchanged")

    model_config = {
        "json_schema_extra": {
            "examples": [{"name": None, "product_type": None, "price": None}]
        }
    }

class ProductIngredientResponse(BaseModel):
#This is never used directly by an endpoint. It's nested inside ProductResponse. Represents one row from product_ingredients bridge table:
    position: int
    ingredient: IngredientResponse

    class Config:
        from_attributes = True

class ProductResponse(ProductBase):
    id: int
    owner_id: Optional[int] = None #bcs when migrating data, there're load of products with no owner
    product_ingredients: List[ProductIngredientResponse] = []

    class Config:
        from_attributes = True

class ProductSummaryResponse(ProductBase): #basically response with no ingredients
    id: int
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True


# INGREDIENT CONFLICT

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


# AUTH

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, description="Leave out to keep unchanged")
    email: Optional[EmailStr] = Field(None, description="Leave out to keep unchanged")
    current_password: Optional[str] = Field(None, description="Leave out to keep unchanged")
    new_password: Optional[str] = Field(None, description="Leave out to keep unchanged")

    model_config = {
        "json_schema_extra": {
            "examples": [{"username": None, "email": None, "current_password": None, "new_password": None}]
        }
    }


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel): #used when returning token after succesful login. User stores this token and send it with every protected request
    access_token: str
    token_type: str = "bearer" 
    #token_type is always "bearer" — this is the OAuth2 standard. The client stores access_token and sends it in every subsequent request as Authorization: Bearer <token>.


# SKIN PROFILE

class SkinProfileCreate(BaseModel):
    skin_type: SkinTypeEnum
    concern_ids: Optional[List[int]] = None

class SkinProfileUpdate(BaseModel):
    skin_type: Optional[SkinTypeEnum] = Field(None, description="Leave out to keep unchanged")
    concern_ids: Optional[List[int]] = Field(None, description="Leave out to keep unchanged")

    model_config = {
        "json_schema_extra": {
            "examples": [{"skin_type": None, "concern_ids": None}]
        }
    }

class SkinProfileResponse(BaseModel):
    id: int
    skin_type: SkinTypeEnum
    concerns: List[SkinConcernResponse] = []

    class Config:
        from_attributes = True


# ANALYTICS

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