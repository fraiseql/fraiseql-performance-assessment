# Phase 4: Data Volume Scaling

## Objective

Scale the benchmark database from ~100-500 records to production-realistic volumes (10K+ users, 100K+ posts, 500K+ comments) to properly stress database indexes, memory pressure, and query optimization differences between frameworks.

## Context

**Current State:**
- `03-data.sql` seeds minimal data (~100 users, ~500 posts, ~2000 comments)
- Small datasets fit entirely in PostgreSQL buffer cache
- Index performance differences not visible
- Memory pressure not tested
- Pagination performance untested

**Target State:**
- 10,000+ users with varied profile data
- 100,000+ posts with realistic content lengths
- 500,000+ comments with threading
- 50,000+ follow relationships (social graph)
- Realistic JSONB profile data for GIN index testing
- Data generation reproducible via seed value

## Files to Modify/Create

| File | Action | Purpose |
|------|--------|---------|
| `database/03-data.sql` | Replace | Minimal seed for quick dev testing |
| `database/04-large-dataset.sql` | Create | Stored procedure for large data generation |
| `database/seed-generator.py` | Create | Python script for configurable data volumes |
| `tests/perf/datasets/` | Create | Pre-generated CSV datasets for JMeter |
| `docker-compose.yml` | Update | Add data volume configuration |
| `Makefile` | Update | Add seed-large, seed-small targets |

## Implementation Steps

### Step 1: Create Scalable Data Generator

```python
# database/seed-generator.py
"""
Configurable benchmark data generator.
Generates realistic social media data at scale.
"""
import argparse
import random
import uuid
import json
from datetime import datetime, timedelta
from faker import Faker
import psycopg

fake = Faker()
Faker.seed(42)  # Reproducible data
random.seed(42)

class DataGenerator:
    def __init__(self, conn_string: str):
        self.conn = psycopg.connect(conn_string)
        self.user_ids = []
        self.post_ids = []

    def generate_users(self, count: int, batch_size: int = 1000):
        """Generate users with varied profile data"""
        print(f"Generating {count} users...")

        for batch_start in range(0, count, batch_size):
            batch_end = min(batch_start + batch_size, count)
            users = []

            for i in range(batch_start, batch_end):
                user_id = uuid.uuid4()
                self.user_ids.append(user_id)

                # First 100 users get predictable UUIDs for testing
                if i < 100:
                    user_id = uuid.UUID(f"{i+1:08d}-1111-1111-1111-111111111111")

                users.append({
                    "id": user_id,
                    "email": fake.unique.email(),
                    "username": fake.unique.user_name()[:100],
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "bio": fake.text(max_nb_chars=500) if random.random() > 0.3 else None,
                    "avatar_url": fake.image_url() if random.random() > 0.2 else None,
                    "is_active": random.random() > 0.05,
                    "created_at": fake.date_time_between(start_date="-2y", end_date="now"),
                })

            self._insert_users_batch(users)
            print(f"  Users: {batch_end}/{count}")

    def generate_posts(self, count: int, batch_size: int = 1000):
        """Generate posts with realistic content"""
        print(f"Generating {count} posts...")

        statuses = ["published"] * 80 + ["draft"] * 15 + ["archived"] * 5

        for batch_start in range(0, count, batch_size):
            batch_end = min(batch_start + batch_size, count)
            posts = []

            for i in range(batch_start, batch_end):
                post_id = uuid.uuid4()
                self.post_ids.append(post_id)

                # First 100 posts get predictable UUIDs
                if i < 100:
                    post_id = uuid.UUID(f"{i+1:08d}-2222-2222-2222-222222222222")

                status = random.choice(statuses)
                created_at = fake.date_time_between(start_date="-1y", end_date="now")

                posts.append({
                    "id": post_id,
                    "author_id": random.choice(self.user_ids),
                    "title": fake.sentence(nb_words=random.randint(4, 12)),
                    "content": fake.text(max_nb_chars=random.randint(200, 5000)),
                    "excerpt": fake.text(max_nb_chars=200),
                    "status": status,
                    "published_at": created_at if status == "published" else None,
                    "created_at": created_at,
                })

            self._insert_posts_batch(posts)
            print(f"  Posts: {batch_end}/{count}")

    def generate_comments(self, count: int, batch_size: int = 5000):
        """Generate comments with threading"""
        print(f"Generating {count} comments...")

        comment_ids = []

        for batch_start in range(0, count, batch_size):
            batch_end = min(batch_start + batch_size, count)
            comments = []

            for i in range(batch_start, batch_end):
                comment_id = uuid.uuid4()

                # First 100 comments get predictable UUIDs
                if i < 100:
                    comment_id = uuid.UUID(f"{i+1:08d}-3333-3333-3333-333333333333")

                # 20% of comments are replies to existing comments
                parent_id = None
                if comment_ids and random.random() < 0.2:
                    parent_id = random.choice(comment_ids[-1000:])  # Reply to recent comments

                comments.append({
                    "id": comment_id,
                    "post_id": random.choice(self.post_ids),
                    "author_id": random.choice(self.user_ids),
                    "parent_id": parent_id,
                    "content": fake.text(max_nb_chars=random.randint(50, 1000)),
                    "is_approved": random.random() > 0.05,
                    "created_at": fake.date_time_between(start_date="-6m", end_date="now"),
                })

                comment_ids.append(comment_id)

            self._insert_comments_batch(comments)
            print(f"  Comments: {batch_end}/{count}")

    def generate_follows(self, count: int, batch_size: int = 5000):
        """Generate follow relationships (social graph)"""
        print(f"Generating {count} follow relationships...")

        follows = set()
        attempts = 0
        max_attempts = count * 3

        while len(follows) < count and attempts < max_attempts:
            follower = random.choice(self.user_ids)
            following = random.choice(self.user_ids)

            if follower != following and (follower, following) not in follows:
                follows.add((follower, following))

            attempts += 1

        follows_list = list(follows)
        for batch_start in range(0, len(follows_list), batch_size):
            batch = follows_list[batch_start:batch_start + batch_size]
            self._insert_follows_batch(batch)
            print(f"  Follows: {min(batch_start + batch_size, len(follows_list))}/{len(follows_list)}")

    def generate_likes(self, count: int, batch_size: int = 5000):
        """Generate post likes"""
        print(f"Generating {count} post likes...")

        likes = set()
        reaction_types = ["like"] * 70 + ["love"] * 20 + ["laugh"] * 8 + ["angry"] * 2

        while len(likes) < count:
            user_id = random.choice(self.user_ids)
            post_id = random.choice(self.post_ids)

            if (user_id, post_id) not in likes:
                likes.add((user_id, post_id))

        likes_list = [(u, p, random.choice(reaction_types)) for u, p in likes]
        for batch_start in range(0, len(likes_list), batch_size):
            batch = likes_list[batch_start:batch_start + batch_size]
            self._insert_likes_batch(batch)
            print(f"  Likes: {min(batch_start + batch_size, len(likes_list))}/{len(likes_list)}")

    def generate_profiles(self):
        """Generate JSONB profile data for all users"""
        print(f"Generating user profiles...")

        profiles = []
        for user_id in self.user_ids:
            profile_data = {
                "location": fake.city() if random.random() > 0.3 else None,
                "website": fake.url() if random.random() > 0.5 else None,
                "social_links": {
                    "twitter": f"@{fake.user_name()}" if random.random() > 0.6 else None,
                    "github": fake.user_name() if random.random() > 0.7 else None,
                },
                "interests": random.sample(
                    ["tech", "sports", "music", "art", "travel", "food", "gaming", "reading"],
                    k=random.randint(0, 4)
                ),
            }

            settings = {
                "email_notifications": random.choice([True, False]),
                "dark_mode": random.choice([True, False]),
                "language": random.choice(["en", "fr", "de", "es"]),
            }

            profiles.append({
                "user_id": user_id,
                "profile_data": json.dumps(profile_data),
                "settings": json.dumps(settings),
                "metadata": json.dumps({"version": 1}),
            })

        self._insert_profiles_batch(profiles)
        print(f"  Profiles: {len(profiles)}")

    # Batch insert methods omitted for brevity - use COPY for performance

    def run(self, config: dict):
        """Run full data generation"""
        print(f"Starting data generation with config: {config}")

        self.generate_users(config["users"])
        self.generate_posts(config["posts"])
        self.generate_comments(config["comments"])
        self.generate_follows(config["follows"])
        self.generate_likes(config["likes"])
        self.generate_profiles()

        # Sync TV tables for FraiseQL
        self._sync_tv_tables()

        # Refresh materialized views
        self._refresh_views()

        # Analyze tables for query planner
        self._analyze_tables()

        print("Data generation complete!")

# Configuration presets
PRESETS = {
    "small": {"users": 100, "posts": 500, "comments": 2000, "follows": 200, "likes": 1000},
    "medium": {"users": 1000, "posts": 5000, "comments": 20000, "follows": 5000, "likes": 10000},
    "large": {"users": 10000, "posts": 100000, "comments": 500000, "follows": 50000, "likes": 200000},
    "xlarge": {"users": 50000, "posts": 500000, "comments": 2000000, "follows": 200000, "likes": 1000000},
}
```

### Step 2: Create SQL-Based Generator for Docker Init

```sql
-- database/04-large-dataset.sql
-- Generate large dataset using pure SQL (faster than Python for Docker init)

-- Function to generate random text
CREATE OR REPLACE FUNCTION benchmark.random_text(min_len INT, max_len INT)
RETURNS TEXT AS $$
DECLARE
    words TEXT[] := ARRAY['lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur',
                          'adipiscing', 'elit', 'sed', 'do', 'eiusmod', 'tempor',
                          'incididunt', 'ut', 'labore', 'et', 'dolore', 'magna'];
    result TEXT := '';
    target_len INT;
BEGIN
    target_len := min_len + floor(random() * (max_len - min_len + 1))::INT;
    WHILE length(result) < target_len LOOP
        result := result || ' ' || words[1 + floor(random() * array_length(words, 1))::INT];
    END LOOP;
    RETURN trim(result);
END;
$$ LANGUAGE plpgsql;

-- Generate users
INSERT INTO benchmark.users (id, email, username, first_name, last_name, bio, is_active, created_at)
SELECT
    CASE WHEN n <= 100
        THEN (lpad(n::TEXT, 8, '0') || '-1111-1111-1111-111111111111')::UUID
        ELSE uuid_generate_v4()
    END,
    'user' || n || '@benchmark.test',
    'user_' || n,
    'First' || (n % 1000),
    'Last' || (n % 500),
    CASE WHEN random() > 0.3 THEN benchmark.random_text(50, 500) ELSE NULL END,
    random() > 0.05,
    NOW() - (random() * INTERVAL '730 days')
FROM generate_series(1, 10000) AS n;

-- Generate posts (10 per user average)
INSERT INTO benchmark.posts (id, author_id, title, content, status, published_at, created_at)
SELECT
    CASE WHEN n <= 100
        THEN (lpad(n::TEXT, 8, '0') || '-2222-2222-2222-222222222222')::UUID
        ELSE uuid_generate_v4()
    END,
    (SELECT id FROM benchmark.users ORDER BY random() LIMIT 1),
    benchmark.random_text(20, 100),
    benchmark.random_text(200, 5000),
    (ARRAY['published', 'published', 'published', 'published', 'draft'])[1 + floor(random() * 5)::INT],
    CASE WHEN random() > 0.2 THEN NOW() - (random() * INTERVAL '365 days') ELSE NULL END,
    NOW() - (random() * INTERVAL '365 days')
FROM generate_series(1, 100000) AS n;

-- Generate comments (5 per post average)
INSERT INTO benchmark.comments (id, post_id, author_id, content, is_approved, created_at)
SELECT
    CASE WHEN n <= 100
        THEN (lpad(n::TEXT, 8, '0') || '-3333-3333-3333-333333333333')::UUID
        ELSE uuid_generate_v4()
    END,
    (SELECT id FROM benchmark.posts ORDER BY random() LIMIT 1),
    (SELECT id FROM benchmark.users ORDER BY random() LIMIT 1),
    benchmark.random_text(50, 1000),
    random() > 0.05,
    NOW() - (random() * INTERVAL '180 days')
FROM generate_series(1, 500000) AS n;

-- Generate follows
INSERT INTO benchmark.user_follows (follower_id, following_id, created_at)
SELECT DISTINCT ON (follower_id, following_id)
    u1.id,
    u2.id,
    NOW() - (random() * INTERVAL '365 days')
FROM
    benchmark.users u1,
    benchmark.users u2,
    generate_series(1, 5) -- ~5 follows per user
WHERE u1.id != u2.id AND random() < 0.001
LIMIT 50000;

-- Generate likes
INSERT INTO benchmark.post_likes (user_id, post_id, reaction_type, created_at)
SELECT DISTINCT ON (user_id, post_id)
    (SELECT id FROM benchmark.users ORDER BY random() LIMIT 1),
    p.id,
    (ARRAY['like', 'like', 'like', 'love', 'laugh'])[1 + floor(random() * 5)::INT],
    NOW() - (random() * INTERVAL '365 days')
FROM benchmark.posts p, generate_series(1, 2) -- ~2 likes per post
LIMIT 200000;

-- Sync TV tables
SELECT benchmark.fn_sync_tv_user(id) FROM benchmark.tb_user;
SELECT benchmark.fn_sync_tv_post(id) FROM benchmark.tb_post;
SELECT benchmark.fn_sync_tv_comment(id) FROM benchmark.tb_comment;

-- Refresh materialized views
REFRESH MATERIALIZED VIEW benchmark.post_popularity;

-- Analyze for query planner
ANALYZE benchmark.users;
ANALYZE benchmark.posts;
ANALYZE benchmark.comments;
ANALYZE benchmark.user_follows;
ANALYZE benchmark.post_likes;
```

### Step 3: Create JMeter Dataset Files

```bash
# Generate CSV files for JMeter parameterized testing
# tests/perf/datasets/generate-datasets.sh

#!/bin/bash
DB_CONN="postgresql://benchmark:benchmark123@localhost:5434/fraiseql_benchmark"

# User IDs for parameterized queries
psql "$DB_CONN" -t -A -c "
SELECT id FROM benchmark.users ORDER BY random() LIMIT 1000
" > tests/perf/datasets/user_ids.csv

# Post IDs
psql "$DB_CONN" -t -A -c "
SELECT id FROM benchmark.posts WHERE status = 'published' ORDER BY random() LIMIT 1000
" > tests/perf/datasets/post_ids.csv

# Comment IDs
psql "$DB_CONN" -t -A -c "
SELECT id FROM benchmark.comments WHERE is_approved = true ORDER BY random() LIMIT 1000
" > tests/perf/datasets/comment_ids.csv

# Users with many posts (for relationship queries)
psql "$DB_CONN" -t -A -c "
SELECT u.id, COUNT(p.id) as post_count
FROM benchmark.users u
JOIN benchmark.posts p ON u.id = p.author_id
GROUP BY u.id
HAVING COUNT(p.id) > 10
ORDER BY post_count DESC
LIMIT 100
" > tests/perf/datasets/active_users.csv

echo "Datasets generated successfully"
```

### Step 4: Update Docker Compose for Data Volume Selection

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: fraiseql_benchmark
      POSTGRES_USER: benchmark
      POSTGRES_PASSWORD: benchmark123
      # Data volume selector
      DATA_VOLUME: ${DATA_VOLUME:-small}
    volumes:
      - ./database/01-extensions.sql:/docker-entrypoint-initdb.d/01-extensions.sql
      - ./database/02-schema.sql:/docker-entrypoint-initdb.d/02-schema.sql
      - ./database/fraiseql_cqrs_schema.sql:/docker-entrypoint-initdb.d/03-cqrs.sql
      - ./database/03-data.sql:/docker-entrypoint-initdb.d/04-small-data.sql
      # Large dataset only loaded if DATA_VOLUME=large
      - ./database/04-large-dataset.sql:/docker-entrypoint-initdb.d/05-large-data.sql:ro
```

### Step 5: Add Makefile Targets

```makefile
# Makefile additions

.PHONY: seed-small seed-medium seed-large seed-xlarge

seed-small:
	docker-compose down -v
	DATA_VOLUME=small docker-compose up -d postgres
	@echo "Seeded small dataset (100 users, 500 posts)"

seed-large:
	docker-compose down -v
	docker-compose up -d postgres
	docker-compose exec postgres psql -U benchmark -d fraiseql_benchmark -f /scripts/04-large-dataset.sql
	@echo "Seeded large dataset (10K users, 100K posts)"

seed-xlarge:
	docker-compose down -v
	docker-compose up -d postgres
	python database/seed-generator.py --preset xlarge
	@echo "Seeded xlarge dataset (50K users, 500K posts)"

generate-jmeter-datasets:
	bash tests/perf/datasets/generate-datasets.sh

db-stats:
	docker-compose exec postgres psql -U benchmark -d fraiseql_benchmark -c "
		SELECT
			relname as table,
			n_live_tup as rows,
			pg_size_pretty(pg_total_relation_size(relid)) as size
		FROM pg_stat_user_tables
		WHERE schemaname = 'benchmark'
		ORDER BY n_live_tup DESC;
	"
```

## Verification Commands

```bash
# Verify data volume after seeding
make db-stats

# Expected output for large dataset:
#    table    |  rows   |  size
# ------------+---------+---------
#  comments   | 500000  | 150 MB
#  posts      | 100000  | 80 MB
#  post_likes | 200000  | 12 MB
#  user_follows| 50000  | 3 MB
#  users      | 10000   | 2 MB

# Verify TV tables synced
docker-compose exec postgres psql -U benchmark -d fraiseql_benchmark -c "
SELECT
    'tv_user' as table, COUNT(*) FROM benchmark.tv_user
UNION ALL SELECT
    'tv_post', COUNT(*) FROM benchmark.tv_post
UNION ALL SELECT
    'tv_comment', COUNT(*) FROM benchmark.tv_comment;
"

# Verify indexes are being used
docker-compose exec postgres psql -U benchmark -d fraiseql_benchmark -c "
EXPLAIN ANALYZE SELECT * FROM benchmark.posts WHERE author_id = '00000001-1111-1111-1111-111111111111';
"
# Should show: Index Scan using idx_posts_author_id
```

## Acceptance Criteria

- [ ] Large dataset contains 10K+ users, 100K+ posts, 500K+ comments
- [ ] Data generation is reproducible (same seed = same data)
- [ ] TV tables automatically synced after generation
- [ ] JMeter datasets (CSV files) generated from actual data
- [ ] Indexes used for common query patterns (EXPLAIN shows Index Scan)
- [ ] Database size > 200MB for large dataset
- [ ] `make seed-large` completes in < 5 minutes

## DO NOT

- Generate data that doesn't fit the schema constraints
- Skip ANALYZE after bulk inserts (query planner needs stats)
- Create datasets without predictable test IDs (first 100 of each entity)
- Forget to sync TV tables after data generation
- Use random() without seed (non-reproducible data)

## Dependencies

```txt
# Python requirements for seed-generator.py
faker>=22.0.0
psycopg[binary]>=3.1.0
```

## Estimated Complexity

**Medium** - Mostly data generation scripts, but requires careful testing of index usage and TV table sync.
