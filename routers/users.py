from fastapi import APIRouter
from schemas import PostResponse, UserCreate, UserResponse, UserUpdate
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Annotated
import models
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()

#create user
@router.post("/create", response_model=UserResponse)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.email == user.email))

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = models.User(email=user.email)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

#get user details
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession , Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

#update user
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    existing_user = result.scalars().first()

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    email_result = await db.execute(select(models.User).where(models.User.email == user.email))

    existing_email = email_result.scalars().first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    if user.email:
        existing_user.email = user.email

    if user.image_file:
        existing_user.image_file = user.image_file
    
    await db.commit()
    await db.refresh(existing_user)
    return existing_user

#get all posts of user
@router.get("/posts/{user_id}", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
    all_posts = result.scalars().all()
    return all_posts

