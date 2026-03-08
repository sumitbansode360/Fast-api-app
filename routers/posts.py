from fastapi import APIRouter
from schemas import PostCreate, PostResponse, PostUpdate, postUpdateParitial
from fastapi import Depends, FastAPI, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Annotated
import models
from database import Base, engine, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from auth import CurrentUser

router = APIRouter()

#get post
@router.get("", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)], current_user: CurrentUser):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()
    return posts 

#create post
@router.post("/create", response_model=PostResponse)
async def create_post(post: PostCreate, db: Annotated[AsyncSession, Depends(get_db)], current_user: CurrentUser):
    result = await db.execute(select(models.User).where(models.User.id == current_user.id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = current_user.id
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])
    return new_post


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id:int, db: Annotated[AsyncSession, Depends(get_db)], current_user: CurrentUser):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id).options(selectinload(models.Post.author)))
    post = result.scalars().first()
    return post

#update post partial
@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(post_id: int, post_data: postUpdateParitial, db: Annotated[AsyncSession, Depends(get_db)], current_user: CurrentUser):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to update this post"
        )
    update_data = post_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)
    
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post

#update post fully
@router.put("/{post_id}", response_model=PostResponse)
async def update_post_fully(post_id: int, post_data: PostUpdate, db: Annotated[AsyncSession, Depends(get_db)], current_user: CurrentUser):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to update this post"
        )

    update_data = post_data.model_dump()
    for key, value in update_data.items():
        setattr(post, key, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post

#delete post
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def post_delete(post_id: int, db: Annotated[AsyncSession, Depends(get_db)], current_user: CurrentUser):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to delete this post"
        )
    await db.delete(post)
    await db.commit()
