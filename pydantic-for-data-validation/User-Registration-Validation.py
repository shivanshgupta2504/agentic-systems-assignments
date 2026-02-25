"""
Part 1: User Registration Validation
Create a Pydantic model UserRegister with:
username (str, min 5 characters)
email (valid email)
age (int, must be ≥ 18)
Validate incoming data and reject invalid inputs.
"""

from pydantic import BaseModel, Field, EmailStr

class UserRegister(BaseModel):
    username: str = Field(description="Username of the user", min_length=5)
    email: EmailStr = Field(description="Email address of the user")
    age: int = Field(description="Age of the user", ge=18)

user_register = UserRegister(username="redswan", email="shivansh@gmail.com", age=18)
print(user_register)

