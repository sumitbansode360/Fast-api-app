from fastapi import Depends, FastAPI, HTTPException, Request, status
from sqlalchemy import select
from typing import Annotated
from sqlalchemy.orm import Session
import models
from database import Base, engine, get_db
from schemas import PostCreate, PostResponse, PostUpdate, postUpdateParitial, UserCreate, UserResponse, UserUpdate
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

@app.get("/")
async def root():
    return {"message": "Hello World"}   

#create user
@app.post("/api/users/create", response_model=UserResponse)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.email == user.email))

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = models.User(email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

#get user details
@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

#update user
@app.patch("/api/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    existing_user = result.scalars().first()

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    email_result = db.execute(select(models.User).where(models.User.email == user.email))

    existing_email = email_result.scalars().first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    if user.email:
        existing_user.email = user.email

    if user.image_file:
        existing_user.image_file = user.image_file
    
    db.commit()
    db.refresh(existing_user)
    return existing_user

#get all posts of user
@app.get("/api/users/posts/{user_id}", response_model=list[PostResponse])
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    all_posts = result.scalars().all()
    return all_posts

#create post
@app.post("/api/posts/create/", response_model=PostResponse)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = post.user_id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

# get post
@app.get("/api/posts/", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts  

#update post partial
@app.patch("/api/posts/{post_id}", response_model=PostResponse)
def update_post_partial(post_id: int, post_data: postUpdateParitial, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    update_data = post_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)
    
    db.commit()
    db.refresh(post)
    return post

#update post fully
@app.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post_fully(post_id: int, post_data: PostUpdate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    update_data = post_data.model_dump()
    for key, value in update_data.items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)
    return post

#delete post
@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_delete(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    db.delete(post)
    db.commit()
