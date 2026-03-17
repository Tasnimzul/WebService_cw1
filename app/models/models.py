from sqlalchemy import (Column, Integer, String, Float, ForeignKey, Table, Boolean, CheckConstraint, UniqueConstraint)
from sqlalchemy.orm import relationship
from app.database import Base

# ─────────────────────────────────────────
# BRIDGE TABLES
# ─────────────────────────────────────────

# SkinConcern ↔ Ingredient (recommended ingredients per concern)
concern_ingredient = Table(
    'concern_ingredients', Base.metadata,
    Column('concern_id', ForeignKey('skin_concerns.id'), primary_key=True),
    Column('ingredient_id', ForeignKey('ingredients.id'), primary_key=True)
)

# SkinProfile ↔ SkinConcern (user has many concerns)
profile_concern = Table(
    'profile_concerns', Base.metadata,
    Column('profile_id', ForeignKey('skin_profiles.id'), primary_key=True),
    Column('concern_id', ForeignKey('skin_concerns.id'), primary_key=True)
)

# ─────────────────────────────────────────
# SKIN CONCERN
# from skin concern dataset
# ─────────────────────────────────────────

class SkinConcern(Base):
    __tablename__ = 'skin_concerns'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100),  nullable=False)
    # Acne, Dark Circles, Dark Spots, Dullness etc
    skin_type = Column(String(50), nullable=False)

    recommended_ingredients = relationship('Ingredient', secondary=concern_ingredient, back_populates='recommended_for')
    profiles = relationship('SkinProfile', secondary=profile_concern, back_populates='concerns')

    __table_args__ = (
        UniqueConstraint('name', 'skin_type', name='unique_concern_per_skintype'),
    ) #same concern can't be duplicated for the same skin type, but CAN exist across different skin types:

# ─────────────────────────────────────────
# INGREDIENT
# from both datasets
# ─────────────────────────────────────────

class Ingredient(Base):
    __tablename__ = 'ingredients'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    irritation_level = Column(String(10), default='low')

    used_in_products = relationship('ProductIngredient', back_populates='ingredient')
    recommended_for = relationship('SkinConcern', secondary=concern_ingredient, back_populates='recommended_ingredients')
    conflicts_as_first = relationship('IngredientConflict', foreign_keys='IngredientConflict.ingredient_1_id', back_populates='ingredient_1')
    conflicts_as_second = relationship('IngredientConflict', foreign_keys='IngredientConflict.ingredient_2_id', back_populates='ingredient_2')

# ─────────────────────────────────────────
# PRODUCT
# from lookfantastic dataset
# ─────────────────────────────────────────

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    product_type = Column(String(100), nullable=True)
    price = Column(Float, nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    owner = relationship('User', backref='products')
    product_ingredients = relationship('ProductIngredient', back_populates='product', cascade='all, delete-orphan')

# ─────────────────────────────────────────
# PRODUCT INGREDIENT
# ─────────────────────────────────────────

class ProductIngredient(Base):
    __tablename__ = 'product_ingredients'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)
    position = Column(Integer, nullable=False)

    product = relationship('Product', back_populates='product_ingredients')
    ingredient = relationship('Ingredient', back_populates='used_in_products')

# ─────────────────────────────────────────
# INGREDIENT CONFLICT
# manually curated
# ─────────────────────────────────────────

class IngredientConflict(Base):
    __tablename__ = 'ingredient_conflicts'

    id = Column(Integer, primary_key=True, index=True)
    ingredient_1_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)
    ingredient_2_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)
    severity = Column(String(10), nullable=False)

    ingredient_1 = relationship('Ingredient', foreign_keys=[ingredient_1_id], back_populates='conflicts_as_first')
    ingredient_2 = relationship('Ingredient', foreign_keys=[ingredient_2_id], back_populates='conflicts_as_second')

    __table_args__ = (
        CheckConstraint('ingredient_1_id != ingredient_2_id', name='check_different_ingredients'),
        UniqueConstraint('ingredient_1_id', 'ingredient_2_id', name='unique_conflict_pair'),
    )

# ─────────────────────────────────────────
# USER
# ─────────────────────────────────────────

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    profile = relationship('SkinProfile', back_populates='user', uselist=False)

# ─────────────────────────────────────────
# SKIN PROFILE
# user generated — one per user
# ─────────────────────────────────────────

class SkinProfile(Base):
    __tablename__ = 'skin_profiles'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    skin_type = Column(String(50), nullable=False)
    # oily / dry / combination / sensitive / normal

    user = relationship('User', back_populates='profile')
    concerns = relationship('SkinConcern', secondary=profile_concern, back_populates='profiles')