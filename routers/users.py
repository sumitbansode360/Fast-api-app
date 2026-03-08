from fastapi import APIRouter, status
from schemas import PostResponse, UserCreate, UserResponse, UserUpdate, Token, CurrentUser
from fastapi import Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Annotated
import models
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from auth import create_access_token, hash_password, oauth2_scheme, verify_access_token, verify_password
from config import settings

router = APIRouter()

#login api 
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # lookup email
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == form_data.username.lower()
        )
    )
    user = result.scalars().first()

    # verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Email or Password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    #create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

# get current logged in user 
@router.get("/me", response_model=CurrentUser)
async def get_current_usr(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """ Get the currently authenticated user. """
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Validate user_id is a valid integer (defense against malformed JWT)
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(
        select(models.User).where(models.User.id == user_id_int)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user 

#create user
@router.post("/create", response_model=UserResponse)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(func.lower(models.User.email) == user.email.lower()))

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = models.User(
        email=user.email,
        password_hash=hash_password(user.password)
    )
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

