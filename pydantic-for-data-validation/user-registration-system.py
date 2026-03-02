"""
Part 1: You are building a User Registration System for an e-commerce platform.
Design a Pydantic model system with the following requirements:

Address Model
city → string (minimum length 3)
pincode → string (must be exactly 6 digits)

User Model
user_id → integer
name → string
email → email string
age → integer (must be ≥ 18)
address → nested Address model
is_premium → optional boolean (default = False)
Assignment validation should be enabled
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict

class Address(BaseModel):
    city: str = Field(min_length=3, description="City in which the address belongs.")
    pincode: str = Field(min_length=6, max_length=6, description="Pincode in which the address belongs.", pattern=r"\d{6}$")

class User(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    user_id: int = Field(description="User ID.")
    name: str = Field(description="User name.")
    email: EmailStr = Field(description="User email address.")
    age: int = Field(description="User age.", ge=18)
    address: Address = Field(description="User address.")
    is_premium: bool = Field(default=False, description="Is it a premium user?")

