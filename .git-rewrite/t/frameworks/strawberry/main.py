#!/usr/bin/env python3
"""
Async GraphQL Benchmarking Server for Strawberry with DataLoader
Uses asyncpg connection pooling and DataLoader to prevent N+1 queries.
"""

import os
from typing import Optional, List
from dataclasses import dataclass

import strawberry
from strawberry.fastapi import GraphQLRouter, BaseContext
from strawberry.dataloader import DataLoader
from fastapi import FastAPI

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.async_db import AsyncDatabase


# DataLoader functions for batching
async def load_users_batch(keys: List[str], db: AsyncDatabase) -> List[Optional[dict]]:
    """Batch load users by IDs."""
    result = await db.fetch(
        "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = ANY($1)",
        keys
    )
    # Create a map for O(1) lookup
    user_map = {user["id"]: user for user in result}
    # Return in the same order as keys
    return [user_map.get(key) for key in keys]


async def load_posts_batch(keys: List[str], db: AsyncDatabase) -> List[Optional[dict]]:
    """Batch load posts by IDs."""
    result = await db.fetch(
        "SELECT id, title, content, author_id FROM benchmark.posts WHERE id = ANY($1)",
        keys
    )
    post_map = {post["id"]: post for post in result}
    return [post_map.get(key) for key in keys]


async def load_posts_by_author_batch(keys: List[str], db: AsyncDatabase) -> List[List[dict]]:
    """Batch load posts by author IDs."""
    result = await db.fetch(
        """
        SELECT id, title, content, author_id
        FROM benchmark.posts
        WHERE author_id = ANY($1)
        ORDER BY author_id, created_at DESC
        """,
        keys
    )

    # Group by author_id
    posts_by_author = {key: [] for key in keys}
    for post in result:
        posts_by_author[post["author_id"]].append(post)

    return [posts_by_author[key] for key in keys]


async def load_comments_by_post_batch(keys: List[str], db: AsyncDatabase) -> List[List[dict]]:
    """Batch load comments by post IDs."""
    result = await db.fetch(
        """
        SELECT id, content, post_id, author_id
        FROM benchmark.comments
        WHERE post_id = ANY($1)
        ORDER BY post_id, created_at DESC
        """,
        keys
    )

    # Group by post_id
    comments_by_post = {key: [] for key in keys}
    for comment in result:
        comments_by_post[comment["post_id"]].append(comment)

    return [comments_by_post[key][:50] for key in keys]  # Limit 50 per post


@strawberry.type
class Comment:
    id: str
    content: str
    author_id: Optional[str] = strawberry.field(default=None)
    post_id: Optional[str] = strawberry.field(default=None)

    @strawberry.field
    async def author(self, info) -> Optional["User"]:
        if not self.author_id:
            return None
        user_data = await info.context.user_loader.load(self.author_id)
        if user_data:
            return User(
                id=user_data["id"],
                username=user_data["username"],
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                bio=user_data.get("bio"),
            )
        return None

    @strawberry.field
    async def post(self, info) -> Optional["Post"]:
        if not self.post_id:
            return None
        post_data = await info.context.post_loader.load(self.post_id)
        if post_data:
            return Post(
                id=post_data["id"],
                title=post_data["title"],
                content=post_data.get("content"),
                author_id=post_data.get("author_id"),
            )
        return None


@strawberry.type
class Post:
    id: str
    title: str
    content: Optional[str] = None
    author_id: Optional[str] = strawberry.field(default=None)

    @strawberry.field
    async def author(self, info) -> Optional["User"]:
        if not self.author_id:
            return None
        user_data = await info.context.user_loader.load(self.author_id)
        if user_data:
            return User(
                id=user_data["id"],
                username=user_data["username"],
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                bio=user_data.get("bio"),
            )
        return None

    @strawberry.field
    async def comments(self, info, limit: int = 50) -> List["Comment"]:
        comments_data = await info.context.comments_by_post_loader.load(self.id)
        return [
            Comment(
                id=comment["id"],
                content=comment["content"],
                author_id=comment.get("author_id"),
                post_id=comment.get("post_id"),
            )
            for comment in comments_data[:limit]
        ]


@strawberry.type
class User:
    id: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None

    @strawberry.field
    async def posts(self, info, limit: int = 50) -> List[Post]:
        posts_data = await info.context.posts_by_author_loader.load(self.id)
        return [
            Post(
                id=post["id"],
                title=post["title"],
                content=post.get("content"),
                author_id=post.get("author_id"),
            )
            for post in posts_data[:limit]
        ]


@strawberry.type
class Query:
    @strawberry.field
    async def ping(self) -> str:
        return "pong"

    @strawberry.field
    async def user(self, info, id: str) -> Optional[User]:
        db = info.context.db
        result = await db.fetchrow(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = $1",
            id
        )
        if result:
            return User(
                id=result["id"],
                username=result["username"],
                first_name=result.get("first_name"),
                last_name=result.get("last_name"),
                bio=result.get("bio"),
            )
        return None

    @strawberry.field
    async def users(self, info, limit: int = 10) -> List[User]:
        db = info.context.db
        result = await db.fetch(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users LIMIT $1",
            limit
        )
        return [
            User(
                id=row["id"],
                username=row["username"],
                first_name=row.get("first_name"),
                last_name=row.get("last_name"),
                bio=row.get("bio"),
            )
            for row in result
        ]

    @strawberry.field
    async def post(self, info, id: str) -> Optional[Post]:
        db = info.context.db
        result = await db.fetchrow(
            "SELECT id, title, content, author_id FROM benchmark.posts WHERE id = $1",
            id
        )
        if result:
            return Post(
                id=result["id"],
                title=result["title"],
                content=result.get("content"),
                author_id=result.get("author_id"),
            )
        return None

    @strawberry.field
    async def posts(self, info, limit: int = 10) -> List[Post]:
        db = info.context.db
        result = await db.fetch(
            "SELECT id, title, content, author_id FROM benchmark.posts LIMIT $1",
            limit
        )
        return [
            Post(
                id=row["id"],
                title=row["title"],
                content=row.get("content"),
                author_id=row.get("author_id"),
            )
            for row in result
        ]

    @strawberry.field
    async def comment(self, info, id: str) -> Optional[Comment]:
        db = info.context.db
        result = await db.fetchrow(
            "SELECT id, content, author_id, post_id FROM benchmark.comments WHERE id = $1",
            id
        )
        if result:
            return Comment(
                id=result["id"],
                content=result["content"],
                author_id=result.get("author_id"),
                post_id=result.get("post_id"),
            )
        return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def update_user(
        self,
        info,
        id: str,
        bio: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Optional[User]:
        db = info.context.db

        # Update user
        update_fields = []
        params = [id]
        param_idx = 2

        if bio is not None:
            update_fields.append(f"bio = ${param_idx}")
            params.append(bio)
            param_idx += 1
        if first_name is not None:
            update_fields.append(f"first_name = ${param_idx}")
            params.append(first_name)
            param_idx += 1
        if last_name is not None:
            update_fields.append(f"last_name = ${param_idx}")
            params.append(last_name)
            param_idx += 1

        if update_fields:
            await db.execute(
                f"UPDATE benchmark.users SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = $1",
                *params
            )

        # Return updated user
        result = await db.fetchrow(
            "SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = $1",
            id
        )
        if result:
            return User(
                id=result["id"],
                username=result["username"],
                first_name=result.get("first_name"),
                last_name=result.get("last_name"),
                bio=result.get("bio"),
            )
        return None


schema = strawberry.Schema(query=Query, mutation=Mutation)


class Context(BaseContext):
    def __init__(self, db: AsyncDatabase):
        super().__init__()
        self.db = db
        # Create DataLoaders for batching
        self.user_loader = DataLoader(load_fn=lambda keys: load_users_batch(keys, db))
        self.post_loader = DataLoader(load_fn=lambda keys: load_posts_batch(keys, db))
        self.posts_by_author_loader = DataLoader(load_fn=lambda keys: load_posts_by_author_batch(keys, db))
        self.comments_by_post_loader = DataLoader(load_fn=lambda keys: load_comments_by_post_batch(keys, db))


async def get_context() -> Context:
    """Context factory for each request."""
    return Context(db=app.state.db)


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize database pool on startup."""
    db = AsyncDatabase()
    await db.connect(
        min_size=10,
        max_size=50,
        statement_cache_size=100
    )
    app.state.db = db


@app.on_event("shutdown")
async def shutdown_event():
    """Close database pool on shutdown."""
    await app.state.db.close()


graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "framework": "strawberry"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
