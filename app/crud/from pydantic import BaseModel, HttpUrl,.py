from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List
from datetime import datetime
import re

def generate_slug(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s) # Remove non-alphanumeric characters (except whitespace and hyphens)
    s = re.sub(r'[\s_-]+', '-', s) # Replace whitespace and underscores with a single hyphen
    s = re.sub(r'^-+|-+$', '', s) # Remove leading/trailing hyphens
    return s

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable name of the product")
    url: HttpUrl = Field(..., description="URL of the product page")
    price_selector: str = Field(..., description="CSS selector for the price element")
    name_selector: str = Field(..., description="CSS selector for the product name element on the page")
    slug: Optional[str] = Field(None, min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
                                description="URL-friendly slug. Auto-generated from name if not provided and validated.")
    is_active: bool = True

class ProductCreate(ProductBase):
    @validator('slug', pre=True, always=True)
    def set_slug(cls, v, values):
        if 'name' in values and (v is None or v == ""):
            return generate_slug(values['name'])
        if v: # Validate provided slug
            return generate_slug(v) # Ensure it's cleaned
        return v # Should not happen if name is present

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[HttpUrl] = None
    price_selector: Optional[str] = None
    name_selector: Optional[str] = None
    slug: Optional[str] = Field(None, min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    is_active: Optional[bool] = None

    @validator('slug', pre=True, always=True)
    def update_slug(cls, v, values):
        if v:
            return generate_slug(v)
        # If name is being updated and slug is not, we might want to regenerate slug,
        # but that could be an unexpected side-effect. For now, only update if explicitly provided.
        return v

class ProductInDBBase(ProductBase):
    id: int
    created_at: datetime
    last_checked_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Replaces orm_mode in Pydantic v2

class Product(ProductInDBBase):
    pass

class ProductList(BaseModel):
    products: List[Product]
    total: int