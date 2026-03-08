from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr = Field(max_length=320)

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=64)

class UserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=320)
    image_file: str | None = Field(default=None, max_length=200)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_file: str | None
    image_path: str

class CurrentUser(UserBase):
    email: str

class Token(BaseModel):
    access_token: str 
    token_type : str

class PostBase(BaseModel):
    title: str = Field(min_length=3, max_length=50)
    content: str = Field(min_length=10, max_length=200)

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_posted: datetime
    user_id: int
    author: UserResponse

class PostUpdate(PostBase):
    pass

class postUpdateParitial(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=50)
    content: str | None = Field(default=None, min_length=10, max_length=200)