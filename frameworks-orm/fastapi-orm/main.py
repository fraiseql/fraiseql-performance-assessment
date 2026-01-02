#!/usr/bin/env python3
"""
Traditional ORM Implementation: FastAPI REST with SQLAlchemy 2.0 ORM
- Uses proper relationships and foreign keys
- Declarative relationships (one-to-many, many-to-one)
- Proper ORM session management
- N+1 prevention with joinedload
"""

import os
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query as QueryParam, Depends, HTTPException
from pydantic import BaseModel
import prometheus_client

from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey, Index, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship, selectinload

# Database configuration
DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.getenv('DB_USER', 'benchmark')}:"
    f"{os.getenv('DB_PASSWORD', 'benchmark123')}@"
    f"{os.getenv('DB_HOST', 'postgres')}:"
    f"{os.getenv('DB_PORT', '5432')}/"
    f"{os.getenv('DB_NAME', 'fraiseql_benchmark')}"
)

Base = declarative_base()

# Prometheus metrics
REQUEST_COUNT = prometheus_client.Counter(
    "fastapi_rest_orm_requests_total", "Total requests", ["method", "endpoint"]
)
REQUEST_LATENCY = prometheus_client.Histogram(
    "fastapi_rest_orm_request_duration_seconds",
    "Request latency",
    ["method", "endpoint"],
)


# ============================================================================
# SQLAlchemy ORM Models with Relationships
# ============================================================================


class User(Base):
    """User model with proper ORM relationships"""

    __tablename__ = "tb_user"
    __table_args__ = (Index("idx_user_id", "id"), {"schema": "benchmark"})

    id = Column(String(36), primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan"
    )


class Post(Base):
    """Post model with relationships"""

    __tablename__ = "tb_post"
    __table_args__ = (
        Index("idx_post_id", "id"),
        Index("idx_post_author", "author_id"),
        {"schema": "benchmark"},
    )

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    author_id = Column(String(36), ForeignKey("benchmark.tb_user.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    author = relationship("User", back_populates="posts")
    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )


class Comment(Base):
    """Comment model with relationships"""

    __tablename__ = "tb_comment"
    __table_args__ = (
        Index("idx_comment_id", "id"),
        Index("idx_comment_post", "post_id"),
        Index("idx_comment_author", "author_id"),
        {"schema": "benchmark"},
    )

    id = Column(String(36), primary_key=True)
    content = Column(Text, nullable=False)
    post_id = Column(String(36), ForeignKey("benchmark.tb_post.id"), nullable=False)
    author_id = Column(String(36), ForeignKey("benchmark.tb_user.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")


# ============================================================================
# Database Session Management
# ============================================================================

engine = None
async_session_maker = None


async def init_db():
    """Initialize database"""
    global engine, async_session_maker

    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=50,
        pool_pre_ping=True,
        connect_args={"timeout": 10},
    )

    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, future=True
    )


async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session_maker() as session:
        yield session


# ============================================================================
# Pydantic Models
# ============================================================================


class CommentResponse(BaseModel):
    id: str
    content: str
    author_id: Optional[str] = None
    post_id: Optional[str] = None

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: str
    title: str
    content: Optional[str] = None
    author_id: Optional[str] = None
    author: Optional["UserResponse"] = None
    comments: Optional[list[CommentResponse]] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    posts: Optional[list[PostResponse]] = None

    class Config:
        from_attributes = True


# ============================================================================
# FastAPI Application
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    yield
    # Shutdown
    if engine:
        await engine.dispose()


app = FastAPI(title="FastAPI REST ORM", lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.get("/ping")
async def ping():
    """Ping endpoint for throughput testing"""
    REQUEST_COUNT.labels(method="GET", endpoint="/ping").inc()
    return {"message": "pong"}


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    include: Optional[str] = QueryParam(None),
    session: AsyncSession = Depends(get_session),
):
    """Get user by ID with optional relationships"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users/{user_id}").inc()

    stmt = select(User).where(User.id == user_id)

    # Load relationships based on include parameter
    if include == "posts":
        stmt = stmt.options(selectinload(User.posts))

    result = await session.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.get("/users", response_model=list[UserResponse])
async def list_users(
    limit: int = QueryParam(10, ge=1, le=100),
    offset: int = QueryParam(0, ge=0),
    include: Optional[str] = QueryParam(None),
    session: AsyncSession = Depends(get_session),
):
    """List users"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users").inc()

    stmt = select(User).limit(limit).offset(offset)

    if include == "posts":
        stmt = stmt.options(selectinload(User.posts))

    result = await session.execute(stmt)
    users = result.scalars().all()

    return users


@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    include: Optional[str] = QueryParam(None),
    session: AsyncSession = Depends(get_session),
):
    """Get post by ID"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{post_id}").inc()

    stmt = select(Post).where(Post.id == post_id).options(selectinload(Post.author))

    if include == "comments":
        stmt = stmt.options(selectinload(Post.comments))

    result = await session.execute(stmt)
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


@app.get("/posts", response_model=list[PostResponse])
async def list_posts(
    limit: int = QueryParam(10, ge=1, le=100),
    offset: int = QueryParam(0, ge=0),
    include: Optional[str] = QueryParam(None),
    session: AsyncSession = Depends(get_session),
):
    """List posts"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts").inc()

    stmt = select(Post).options(selectinload(Post.author)).limit(limit).offset(offset)

    if include == "comments":
        stmt = stmt.options(selectinload(Post.comments))

    result = await session.execute(stmt)
    posts = result.scalars().all()

    return posts


@app.get("/users/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(
    user_id: str,
    limit: int = QueryParam(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """Get posts by user"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users/{user_id}/posts").inc()

    stmt = (
        select(Post)
        .where(Post.author_id == user_id)
        .options(selectinload(Post.author))
        .limit(limit)
    )

    result = await session.execute(stmt)
    posts = result.scalars().all()

    return posts


@app.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
async def get_post_comments(
    post_id: str,
    limit: int = QueryParam(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """Get comments for a post"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{post_id}/comments").inc()

    stmt = select(Comment).where(Comment.post_id == post_id).limit(limit)

    result = await session.execute(stmt)
    comments = result.scalars().all()

    return comments


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
