from sqlalchemy import (Column, Integer, String, Float,Text, ForeignKey, Table, Boolean, CheckConstraint, UniqueConstraint)
from sqlalchemy.orm import relationship
from app.database import Base

# ─────────────────────────────────────────
# BRIDGE TABLE
# ─────────────────────────────────────────

concern_ingredient = Table(
    'concern_ingredients', Base.metadata,
    Column('concern_id', ForeignKey('skin_concerns.id'), primary_key=True),
    Column('ingredient_id', ForeignKey('ingredients.id'), primary_key=True)
)


# ─────────────────────────────────────────
# MAIN MODELS

class Ingredient(Base):
    __tablename__ = 'ingredients'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    irritation_level = Column(String(10), default='low')

    used_in_products = relationship('ProductIngredient', back_populates='ingredient')
    recommended_for = relationship('SkinConcern', secondary=concern_ingredient, back_populates='recommended_ingredients')
    conflicts_as_first = relationship('IngredientConflict', foreign_keys='IngredientConflict.ingredient_1_id', back_populates='ingredient_1')
    conflicts_as_second = relationship('IngredientConflict', foreign_keys='IngredientConflict.ingredient_2_id', back_populates='ingredient_2')



class SkinConcern(Base):
    __tablename__ = 'skin_concerns'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    recommended_ingredients = relationship('Ingredient', secondary=concern_ingredient, back_populates='recommended_for')


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    size = Column(String(50), nullable=True)
    loves_count = Column(Integer, nullable=True)

    product_ingredients = relationship('ProductIngredient', back_populates='product', cascade='all, delete-orphan')



class ProductIngredient(Base):
    __tablename__ = 'product_ingredients'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)
    position = Column(Integer, nullable=False)

    product = relationship('Product', back_populates='product_ingredients')
    ingredient = relationship('Ingredient', back_populates='used_in_products')



class IngredientConflict(Base):
    __tablename__ = 'ingredient_conflicts'

    id = Column(Integer, primary_key=True, index=True)
    ingredient_1_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)
    ingredient_2_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)
    severity = Column(String(10), nullable=False)

    ingredient_1 = relationship('Ingredient', foreign_keys=[ingredient_1_id], back_populates='conflicts_as_first')
    ingredient_2 = relationship('Ingredient', foreign_keys=[ingredient_2_id], back_populates='conflicts_as_second')

    __table_args__ = (
        CheckConstraint(
            'ingredient_1_id != ingredient_2_id',
            name='check_different_ingredients'
        ),
        UniqueConstraint(
            'ingredient_1_id',
            'ingredient_2_id',
            name='unique_conflict_pair'
        ),
    )


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)

    profile = relationship('UserProfile', back_populates='user', uselist=False)



user_concerns = Table(
    'user_concerns', Base.metadata,
    Column('user_id', ForeignKey('users.id'), primary_key=True),
    Column('concern_id', ForeignKey('skin_concerns.id'), primary_key=True)
)

# 2. Update UserProfile
class UserProfile(Base):
    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    age_range = Column(String(10), nullable=True)
    budget = Column(Float, nullable=True)

    user = relationship('User', back_populates='profile')
    concerns = relationship('SkinConcern', secondary=user_concerns)