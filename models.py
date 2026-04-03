from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")


class UserRegister(BaseModel):
    """Model for user registration data."""

    email: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=8, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate that the provided email matches the required format."""
        if not EMAIL_REGEX.match(value):
            raise ValueError("Invalid email address.")
        return value.lower()


class TaskCreate(BaseModel):
    """Model for creating a new task."""

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class TaskUpdate(BaseModel):
    """Model for updating an existing task."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: Optional[bool] = None
