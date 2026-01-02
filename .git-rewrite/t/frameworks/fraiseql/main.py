#!/usr/bin/env python3
"""
FraiseQL Comparative Benchmarking Implementation v1.8.1
Optimized GraphQL server using FraiseQL with Rust pipeline for performance testing against other frameworks.
"""

import logging
import os
from typing import Any

import uvicorn
from fastapi import Request

# FraiseQL v1.8.1 imports
import fraiseql
from fraiseql.fastapi import create_fraiseql_app, FraiseQLConfig
from fraiseql.fastapi.config import IntrospectionPolicy
from fraiseql.types import UUID
from graphql import GraphQLResolveInfo


# FraiseQL Configuration
def create_fraiseql_config() -> FraiseQLConfig:
    """Create FraiseQL configuration for benchmarking."""
    return FraiseQLConfig(
        database_url=f"postgresql://{os.getenv('DB_USER', 'benchmark')}:{os.getenv('DB_PASSWORD', 'benchmark123')}@{os.getenv('DB_HOST', 'postgres')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'fraiseql_benchmark')}",
        environment="development",
        introspection_policy=IntrospectionPolicy.PUBLIC,
        enable_playground=True,
        default_query_schema="public",
        default_mutation_schema="benchmark",
        auto_camel_case=True,
        cors_enabled=True,
        complexity_enabled=False,  # Disable for benchmarking
        database_pool_size=20,
        database_max_overflow=10,
        max_query_depth=10,
    )


# FraiseQL GraphQL Types
@fraiseql.type(sql_source="tv_user")
class User:
    id: UUID
    username: str
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None

    # Add posts resolver for compatibility with JMeter tests
    @fraiseql.field
    async def posts(self, info, limit: int = 10) -> list["Post"]:
        """Get posts for this user."""
        db = info.context["db"]
        return await db.find(
            "tv_post", where={"author_id": {"eq": str(self.id)}}, limit=limit
        )


@fraiseql.type(sql_source="tv_post")
class Post:
    id: UUID
    title: str
    content: str
    author: User


@fraiseql.type(sql_source="comments")
class Comment:
    id: UUID
    content: str
    author: User
    post: Post


# FraiseQL Query Resolvers
@fraiseql.query
async def ping(info: GraphQLResolveInfo) -> str:
    """Simple ping query for throughput testing."""
    return "pong"


@fraiseql.query
async def user(info: GraphQLResolveInfo, id: UUID) -> User | None:
    """Get user by ID."""
    db = info.context["db"]
    return await db.find_one("tv_user", id=id)


@fraiseql.query
async def users(info: GraphQLResolveInfo, limit: int = 10) -> list[User]:
    """Get users list with pagination."""
    db = info.context["db"]
    return await db.find("tv_user", limit=limit, order_by=[{"created_at": "DESC"}])


@fraiseql.query
async def posts(info: GraphQLResolveInfo, limit: int = 10) -> list[Post]:
    """Get posts list."""
    db = info.context["db"]
    # For posts, we need to handle the JSON structure
    # Use raw SQL since the data is stored as JSON in tv_post
    sql = """
    SELECT
        data->>'id' as id,
        data->>'title' as title,
        data->>'content' as content,
        json_build_object(
            'id', data->'author'->>'id',
            'username', data->'author'->>'username',
            'first_name', data->'author'->>'fullName'
        ) as author
    FROM benchmark.tv_post
    WHERE data->>'published' = 'true'
    ORDER BY data->>'createdAt' DESC
    LIMIT $1
    """
    return await db.execute(sql, (limit,))


@fraiseql.query
async def comments(info: GraphQLResolveInfo, limit: int = 10) -> list[Comment]:
    """Get comments list."""
    db = info.context["db"]
    # Use raw SQL for JOIN operations
    sql = """
    SELECT c.id, c.content, c.created_at,
           json_build_object('id', u.id, 'username', u.username, 'first_name', u.first_name, 'last_name', u.last_name, 'bio', u.bio) as author,
           json_build_object('id', p.id, 'title', p.title, 'content', p.content) as post
    FROM benchmark.tb_comment c
    JOIN benchmark.tb_user u ON c.author_id = u.id
    JOIN benchmark.tb_post p ON c.post_id = p.id
    WHERE c.is_approved = true
    ORDER BY c.created_at DESC
    LIMIT $1
    """
    return await db.execute(sql, (limit,))


@fraiseql.query
async def post(info: GraphQLResolveInfo, id: UUID) -> Post | None:
    """Get post by ID."""
    db = info.context["db"]

    # Use raw SQL for complex JSON operations
    sql = """
    SELECT
        data->>'id' as id,
        data->>'title' as title,
        data->>'content' as content,
        json_build_object(
            'id', data->'author'->>'id',
            'username', data->'author'->>'username',
            'first_name', data->'author'->>'fullName'
        ) as author
    FROM benchmark.tv_post
    WHERE data->>'id' = $1
    LIMIT 1
    """

    result = await db.execute(sql, (str(id),))
    return result[0] if result else None


@fraiseql.query
async def comment(info: GraphQLResolveInfo, id: UUID) -> Comment | None:
    """Get comment by ID."""
    db = info.context["db"]

    # Use raw SQL for JOIN operations
    sql = """
    SELECT c.id, c.content, c.created_at,
           json_build_object('id', u.id, 'username', u.username) as author,
           json_build_object('id', p.id, 'title', p.title) as post
    FROM benchmark.comments c
    JOIN benchmark.users u ON c.author_id = u.id
    JOIN benchmark.posts p ON c.post_id = p.id
    WHERE c.id = $1 AND c.is_approved = true
    LIMIT 1
    """

    result = await db.execute(sql, (str(id),))
    return result[0] if result else None


# FraiseQL Mutation Resolvers
@fraiseql.mutation
async def update_user(
    info: GraphQLResolveInfo,
    id: UUID,
    first_name: str | None = None,
    last_name: str | None = None,
    bio: str | None = None,
) -> User | None:
    """Update user mutation."""
    db = info.context["db"]

    # Build update data
    update_data = {}
    if first_name is not None:
        update_data["first_name"] = first_name
    if last_name is not None:
        update_data["last_name"] = last_name
    if bio is not None:
        update_data["bio"] = bio

    if update_data:
        update_data["updated_at"] = "NOW()"  # SQL function

        await db.update("tb_user", where={"id": {"eq": str(id)}}, data=update_data)

    # Return updated user data
    return await db.find_one("tv_user", id=id)


# Context getter for FraiseQL
async def get_context(request: Request) -> dict[str, Any]:
    """Context creation for FraiseQL requests."""
    # Return empty context - FraiseQL will inject database automatically
    return {}


# Create FraiseQL app
app = create_fraiseql_app(
    config=create_fraiseql_config(),
    context_getter=get_context,
    title="FraiseQL Comparative Benchmark v1.8.1",
    description="FraiseQL GraphQL server using Rust pipeline for performance testing",
    production=False,
)


# Add additional routes for health and metrics
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "framework": "fraiseql", "version": "1.8.1"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import Response

    return Response(
        media_type="text/plain", content=prometheus_client.generate_latest()
    )


def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=4000, log_level="info")


if __name__ == "__main__":
    main()
