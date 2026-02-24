from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr = Field(max_length=320)

class UserCreate(UserBase):
    # password: str = Field(min_length=8, max_length=64)
    pass

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_file: str | None
    image_path: str


class PostBase(BaseModel):
    title: str = Field(min_length=3, max_length=50)
    content: str = Field(min_length=10, max_length=200)

class PostCreate(PostBase):
    user_id: int # temp

class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_posted: datetime
    user_id: int
    author: UserResponse