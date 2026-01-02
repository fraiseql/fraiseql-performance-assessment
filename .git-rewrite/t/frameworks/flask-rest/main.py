#!/usr/bin/env python3
"""
Flask REST Comparative Benchmarking Implementation
Traditional synchronous REST API using psycopg3 connection pool (demonstrates N+1 problem).
"""

import os
from typing import Optional
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from flask import Flask, request, jsonify
import prometheus_client

# Metrics
REQUEST_COUNT = prometheus_client.Counter(
    "flask_rest_requests_total", "Total requests", ["method", "endpoint"]
)
REQUEST_LATENCY = prometheus_client.Histogram(
    "flask_rest_request_duration_seconds", "Request latency", ["method", "endpoint"]
)


# Initialize connection pool globally
pool: Optional[ConnectionPool] = None


def init_pool():
    """Initialize psycopg3 connection pool."""
    global pool

    conninfo = psycopg.conninfo.make_conninfo(
        host=os.getenv("DB_HOST", "postgres"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "fraiseql_benchmark"),
        user=os.getenv("DB_USER", "benchmark"),
        password=os.getenv("DB_PASSWORD", "benchmark123"),
    )

    pool = ConnectionPool(
        conninfo=conninfo,
        min_size=10,
        max_size=50,
        timeout=30.0,
        max_idle=300.0,
        max_lifetime=3600.0,
    )


def close_pool():
    """Close connection pool."""
    global pool
    if pool:
        pool.close()


@contextmanager
def get_db_connection():
    """Get database connection from pool."""
    conn = pool.connection()
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: Optional[tuple] = None):
    """Execute query and return results."""
    with get_db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params or ())
            if cur.description:
                return cur.fetchall()
            return []


app = Flask(__name__)

# Initialize pool when app starts
init_pool()


# Register cleanup on app teardown
@app.teardown_appcontext
def teardown_db(exception=None):
    """Close pool on app shutdown."""
    # Note: This is only called at app shutdown, not per-request
    pass


@app.route("/ping")
def ping():
    """Simple ping endpoint for throughput testing"""
    REQUEST_COUNT.labels(method="GET", endpoint="/ping").inc()
    return jsonify({"message": "pong"})


@app.route("/users")
def list_users():
    """List users (basic info only)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users").inc()

    limit = int(request.args.get("limit", 10))
    users = execute_query(
        """
        SELECT id, username, first_name, last_name, bio
        FROM benchmark.users
        ORDER BY created_at DESC
        LIMIT %s
    """,
        (limit,),
    )

    return jsonify({"users": users})


@app.route("/users/<user_id>")
def get_user(user_id):
    """Get user by ID (basic info only)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users/{id}").inc()

    user = execute_query(
        """
        SELECT id, username, first_name, last_name, bio
        FROM benchmark.users
        WHERE id = %s
    """,
        (user_id,),
    )

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user[0])


@app.route("/users/<user_id>/posts")
def get_user_posts(user_id):
    """Get user's posts (separate endpoint - causes N+1)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users/{id}/posts").inc()

    posts = execute_query(
        """
        SELECT id, title, content
        FROM benchmark.posts
        WHERE author_id = %s AND status = 'published'
        ORDER BY published_at DESC
        LIMIT 10
    """,
        (user_id,),
    )

    return jsonify({"posts": posts})


@app.route("/users/<user_id>/followers")
def get_user_followers(user_id):
    """Get user's followers (separate endpoint)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users/{id}/followers").inc()

    followers = execute_query(
        """
        SELECT u.id, u.username
        FROM benchmark.user_follows uf
        JOIN benchmark.users u ON uf.follower_id = u.id
        WHERE uf.following_id = %s
        LIMIT 10
    """,
        (user_id,),
    )

    return jsonify({"followers": followers})


@app.route("/users/<user_id>/following")
def get_user_following(user_id):
    REQUEST_COUNT.labels(method="GET", endpoint="/users/{id}/following").inc()

    # Get users that this user follows
    result = execute_query(
        """
        SELECT u.id, u.username, u.first_name, u.last_name, u.bio
        FROM benchmark.users u
        JOIN benchmark.user_follows f ON f.following_id = u.id
        WHERE f.follower_id = %s
        LIMIT 10
        """,
        (user_id,),
    )

    return jsonify({"following": result})


@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    REQUEST_COUNT.labels(method="PUT", endpoint="/users/{id}").inc()

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update user
    update_fields = []
    params = []
    if "first_name" in data:
        update_fields.append("first_name = %s")
        params.append(data["first_name"])
    if "last_name" in data:
        update_fields.append("last_name = %s")
        params.append(data["last_name"])
    if "bio" in data:
        update_fields.append("bio = %s")
        params.append(data["bio"])

    if update_fields:
        params.append(user_id)
        execute_query(
            f"UPDATE benchmark.users SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s",
            tuple(params),
        )

    # Return updated user
    return get_user(user_id)


@app.route("/posts")
def list_posts():
    """List posts (basic info only)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts").inc()

    limit = int(request.args.get("limit", 10))
    posts = execute_query(
        """
        SELECT id, title, content
        FROM benchmark.posts
        WHERE status = 'published'
        ORDER BY published_at DESC
        LIMIT %s
    """,
        (limit,),
    )

    return jsonify({"posts": posts})


@app.route("/posts/<post_id>")
def get_post(post_id):
    """Get post by ID (basic info only - matches benchmarking expectations)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{id}").inc()

    post = execute_query(
        """
        SELECT id, title, content
        FROM benchmark.posts
        WHERE id = %s AND status = 'published'
    """,
        (post_id,),
    )

    if not post:
        return jsonify({"error": "Post not found"}), 404

    return jsonify(post[0])


@app.route("/posts/<post_id>/author")
def get_post_author(post_id):
    """Get post's author (separate endpoint - N+1)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{id}/author").inc()

    author = execute_query(
        """
        SELECT u.id, u.username
        FROM benchmark.posts p
        JOIN benchmark.users u ON p.author_id = u.id
        WHERE p.id = %s AND p.status = 'published'
    """,
        (post_id,),
    )

    if not author:
        return jsonify({"error": "Post not found"}), 404

    return jsonify(author[0])


@app.route("/comments/<comment_id>")
def get_comment(comment_id):
    """Get comment by ID (basic info only)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/comments/{id}").inc()

    comment = execute_query(
        """
        SELECT id, content
        FROM benchmark.comments
        WHERE id = %s
    """,
        (comment_id,),
    )

    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    return jsonify(comment[0])


@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "framework": "flask-rest"})


@app.route("/metrics")
def metrics():
    return prometheus_client.generate_latest()


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=8004, debug=False)
    finally:
        close_pool()
