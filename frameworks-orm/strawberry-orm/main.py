#!/usr/bin/env python3
"""
Traditional ORM Implementation: Strawberry GraphQL with SQLAlchemy 2.0 ORM
- Uses proper relationships and foreign keys
- Declarative relationships (one-to-many, many-to-one)
- Proper ORM session management
- N+1 prevention with joinedload and selectinload
"""

import os
from typing import Optional
from datetime import datetime

import strawberry
from strawberry.fastapi import GraphQLRouter, BaseContext
from strawberry.dataloader import DataLoader
from fastapi import FastAPI
from contextlib import asynccontextmanager

from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey, Integer, Index
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship, selectinload, joinedload
from sqlalchemy import select, func

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
    """Post model with relationships to User and Comment"""

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
    """Initialize database engine and session maker"""
    global engine, async_session_maker

    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=50,
        pool_pre_ping=True,
        connect_args={
            "timeout": 10,
            "command_timeout": 10,
        },
    )

    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, future=True
    )


async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session_maker() as session:
        yield session


# ============================================================================
# DataLoader Functions (N+1 Prevention)
# ============================================================================


async def load_users_batch(keys: list[str]) -> list[Optional[dict]]:
    """Batch load users by IDs using ORM"""
    async with async_session_maker() as session:
        stmt = select(User).where(User.id.in_(keys))
        result = await session.execute(stmt)
        users = result.scalars().all()

        user_map = {user.id: user for user in users}
        return [user_map.get(key) for key in keys]


async def load_posts_batch(keys: list[str]) -> list[Optional[dict]]:
    """Batch load posts by IDs with author relationship"""
    async with async_session_maker() as session:
        stmt = select(Post).where(Post.id.in_(keys)).options(selectinload(Post.author))
        result = await session.execute(stmt)
        posts = result.unique().scalars().all()

        post_map = {post.id: post for post in posts}
        return [post_map.get(key) for key in keys]


async def load_posts_by_author_batch(keys: list[str]) -> list[list]:
    """Batch load posts by author IDs using ORM"""
    async with async_session_maker() as session:
        stmt = (
            select(Post)
            .where(Post.author_id.in_(keys))
            .order_by(Post.created_at.desc())
        )
        result = await session.execute(stmt)
        posts = result.scalars().all()

        # Group by author_id
        posts_by_author = {key: [] for key in keys}
        for post in posts:
            posts_by_author[post.author_id].append(post)

        return [posts_by_author[key] for key in keys]


async def load_comments_by_post_batch(keys: list[str]) -> list[list]:
    """Batch load comments by post IDs using ORM"""
    async with async_session_maker() as session:
        stmt = (
            select(Comment)
            .where(Comment.post_id.in_(keys))
            .order_by(Comment.created_at.desc())
        )
        result = await session.execute(stmt)
        comments = result.scalars().all()

        # Group by post_id
        comments_by_post = {key: [] for key in keys}
        for comment in comments:
            comments_by_post[comment.post_id].append(comment)

        return [comments_by_post[key][:50] for key in keys]


# ============================================================================
# GraphQL Types
# ============================================================================


@strawberry.type
class CommentGQL:
    id: str
    content: str
    author_id: Optional[str] = None
    post_id: Optional[str] = None

    @strawberry.field
    async def author(self, info) -> Optional["UserGQL"]:
        if not self.author_id:
            return None
        # Use DataLoader to prevent N+1
        user_loader = info.context.get("user_loader")
        if user_loader:
            user = await user_loader.load(self.author_id)
            if user:
                return UserGQL(
                    id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    bio=user.bio,
                )
        return None


@strawberry.type
class PostGQL:
    id: str
    title: str
    content: Optional[str] = None
    author_id: Optional[str] = None

    @strawberry.field
    async def author(self, info) -> Optional["UserGQL"]:
        if not self.author_id:
            return None
        user_loader = info.context.get("user_loader")
        if user_loader:
            user = await user_loader.load(self.author_id)
            if user:
                return UserGQL(
                    id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    bio=user.bio,
                )
        return None

    @strawberry.field
    async def comments(self, info) -> list[CommentGQL]:
        comments_loader = info.context.get("comments_loader")
        if comments_loader:
            comments = await comments_loader.load(self.id)
            return [
                CommentGQL(
                    id=c.id, content=c.content, author_id=c.author_id, post_id=c.post_id
                )
                for c in comments
            ]
        return []


@strawberry.type
class UserGQL:
    id: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None

    @strawberry.field
    async def posts(self, info) -> list[PostGQL]:
        posts_loader = info.context.get("posts_loader")
        if posts_loader:
            posts = await posts_loader.load(self.id)
            return [
                PostGQL(
                    id=p.id, title=p.title, content=p.content, author_id=p.author_id
                )
                for p in posts
            ]
        return []


# ============================================================================
# GraphQL Queries
# ============================================================================


@strawberry.type
class Query:
    @strawberry.field
    async def user(self, info, id: str) -> Optional[UserGQL]:
        """Get a user by ID"""
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == id)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if not user:
                return None

            return UserGQL(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                bio=user.bio,
            )

    @strawberry.field
    async def users(self, info, limit: int = 10) -> list[UserGQL]:
        """List users"""
        async with async_session_maker() as session:
            stmt = select(User).limit(limit)
            result = await session.execute(stmt)
            users = result.scalars().all()

            return [
                UserGQL(
                    id=u.id,
                    username=u.username,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    bio=u.bio,
                )
                for u in users
            ]

    @strawberry.field
    async def post(self, info, id: str) -> Optional[PostGQL]:
        """Get a post by ID"""
        async with async_session_maker() as session:
            stmt = select(Post).where(Post.id == id).options(selectinload(Post.author))
            result = await session.execute(stmt)
            post = result.scalars().first()

            if not post:
                return None

            return PostGQL(
                id=post.id,
                title=post.title,
                content=post.content,
                author_id=post.author_id,
            )

    @strawberry.field
    async def ping(self) -> str:
        """Simple ping query for throughput testing"""
        return "pong"


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


app = FastAPI(title="Strawberry GraphQL ORM", lifespan=lifespan)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    pass


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Create DataLoader functions for context
async def get_dataloaders(info: BaseContext):
    """Create DataLoaders for the request"""
    return {
        "user_loader": DataLoader(load_users_batch),
        "posts_loader": DataLoader(load_posts_by_author_batch),
        "comments_loader": DataLoader(load_comments_by_post_batch),
    }


# GraphQL router
graphql_router = GraphQLRouter(Query, context_getter=get_dataloaders)

app.include_router(graphql_router, prefix="/graphql")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
