# XS Database Test Run
## Quick Validation Pipeline

**Goal**: Test end-to-end data generation and import in <1 hour

**Data Volume (XS)**:
- 500 users
- 5,000 posts (10 per user)
- 25,000 comments (5 per post)
- 2,500 follows
- 10,000 likes

**Expected Results**:
- SQLite file size: ~150-200 MB
- Generation time: ~15-20 minutes
- PostgreSQL import time: ~1-2 minutes
- Total pipeline time: ~30 minutes

---

## Phase 1: Setup (5 minutes)

### 1.1 Create minimal SQLite schema

File: `database/schema-sqlite-xs.sql`

```sql
-- Minimal schema for XS testing
PRAGMA journal_mode = MEMORY;
PRAGMA synchronous = OFF;
PRAGMA cache_size = 100000;

CREATE TABLE users (
    pk_user INTEGER PRIMARY KEY,
    id TEXT UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    bio TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE posts (
    pk_post INTEGER PRIMARY KEY,
    id TEXT UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    fk_author INTEGER NOT NULL,
    published INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (fk_author) REFERENCES users(pk_user)
);

CREATE TABLE comments (
    pk_comment INTEGER PRIMARY KEY,
    id TEXT UNIQUE NOT NULL,
    identifier TEXT,
    content TEXT NOT NULL,
    fk_post INTEGER NOT NULL,
    fk_author INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (fk_post) REFERENCES posts(pk_post),
    FOREIGN KEY (fk_author) REFERENCES users(pk_user)
);

CREATE TABLE user_follows (
    fk_follower INTEGER NOT NULL,
    fk_following INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (fk_follower, fk_following),
    FOREIGN KEY (fk_follower) REFERENCES users(pk_user),
    FOREIGN KEY (fk_following) REFERENCES users(pk_user),
    CHECK (fk_follower != fk_following)
);

CREATE TABLE post_likes (
    fk_user INTEGER NOT NULL,
    fk_post INTEGER NOT NULL,
    reaction_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (fk_user, fk_post),
    FOREIGN KEY (fk_user) REFERENCES users(pk_user),
    FOREIGN KEY (fk_post) REFERENCES posts(pk_post)
);
```

### 1.2 Create XS generator script

File: `database/xs-generator.py`

```python
#!/usr/bin/env python3
"""
Quick XS database generator for testing the full pipeline.
Generates: 500 users, 5K posts, 25K comments in ~15-20 minutes.
"""

import sqlite3
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

try:
    from faker import Faker
    import requests
    from openai import OpenAI
except ImportError:
    print("Install with: pip install faker requests openai")
    exit(1)


class XSGenerator:
    """Generate XS test dataset"""

    def __init__(self, db_path: str, vllm_endpoint: str = "http://localhost:8000/v1"):
        self.db_path = db_path
        self.vllm_endpoint = vllm_endpoint

        # Initialize database
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode = MEMORY")
        self.conn.execute("PRAGMA synchronous = OFF")

        # Initialize Faker
        self.fake = Faker()
        Faker.seed(42)
        random.seed(42)

        # Initialize vLLM client
        self.client = OpenAI(api_key="none", base_url=vllm_endpoint)

        # Store IDs for relationships
        self.user_ids = []
        self.post_ids = []

    def create_schema(self):
        """Create SQLite schema"""
        print("Creating schema...")
        with open("database/schema-sqlite-xs.sql") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    def generate_users(self, count: int = 500):
        """Generate users with Faker"""
        print(f"Generating {count} users...")

        users = []
        for i in range(count):
            user_id = str(uuid.uuid4())
            self.user_ids.append(i + 1)  # Store pk_user

            users.append((
                i + 1,  # pk_user
                user_id,  # id
                f"user_{i+1:04d}",  # identifier
                self.fake.unique.email(),  # email
                f"user_{i+1}",  # username
                self.fake.name(),  # full_name
                self.fake.text(max_nb_chars=200) if random.random() > 0.3 else None,  # bio
                datetime.now().isoformat(),  # created_at
                datetime.now().isoformat(),  # updated_at
            ))

        cursor = self.conn.cursor()
        cursor.executemany(
            """INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            users
        )
        self.conn.commit()
        print(f"  ✓ {count} users created")

    def generate_posts(self, count: int = 5000):
        """Generate posts: structure with Faker, content with vLLM"""
        print(f"Generating {count} posts...")

        # Step 1: Get vLLM titles in batches
        print(f"  Generating titles from vLLM...")
        titles = self._vllm_batch_titles(count, batch_size=100)

        # Step 2: Get vLLM content in batches
        print(f"  Generating content from vLLM...")
        contents = self._vllm_batch_content(count, batch_size=50)

        # Step 3: Insert posts
        posts = []
        for i in range(count):
            post_id = str(uuid.uuid4())
            self.post_ids.append(i + 1)

            posts.append((
                i + 1,  # pk_post
                post_id,  # id
                f"post_{i+1:05d}",  # identifier
                titles[i],  # title
                contents[i],  # content
                random.choice(self.user_ids),  # fk_author
                1 if random.random() > 0.2 else 0,  # published
                (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),  # created_at
                datetime.now().isoformat(),  # updated_at
            ))

        cursor = self.conn.cursor()
        cursor.executemany(
            """INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            posts
        )
        self.conn.commit()
        print(f"  ✓ {count} posts created")

    def generate_comments(self, count: int = 25000):
        """Generate comments: structure with Faker, content with vLLM"""
        print(f"Generating {count} comments...")

        # Step 1: Get vLLM content in batches
        print(f"  Generating comment content from vLLM...")
        contents = self._vllm_batch_comments(count, batch_size=50)

        # Step 2: Insert comments
        comments = []
        for i in range(count):
            comment_id = str(uuid.uuid4())

            comments.append((
                i + 1,  # pk_comment
                comment_id,  # id
                None,  # identifier
                contents[i],  # content
                random.choice(self.post_ids),  # fk_post
                random.choice(self.user_ids),  # fk_author
                (datetime.now() - timedelta(days=random.randint(0, 180))).isoformat(),  # created_at
                datetime.now().isoformat(),  # updated_at
            ))

        cursor = self.conn.cursor()
        cursor.executemany(
            """INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            comments
        )
        self.conn.commit()
        print(f"  ✓ {count} comments created")

    def generate_relationships(self):
        """Generate follows and likes"""
        print("Generating relationships...")

        # Follows: 2500 (5 per user average)
        follows = []
        for _ in range(2500):
            follower = random.choice(self.user_ids)
            following = random.choice(self.user_ids)

            if follower != following:
                follows.append((
                    follower,
                    following,
                    datetime.now().isoformat()
                ))

        cursor = self.conn.cursor()
        cursor.executemany(
            """INSERT OR IGNORE INTO user_follows VALUES (?, ?, ?)""",
            follows
        )

        # Likes: 10000 (2 per post average)
        likes = []
        for _ in range(10000):
            likes.append((
                random.choice(self.user_ids),
                random.choice(self.post_ids),
                random.choice(['like', 'love', 'laugh']),
                datetime.now().isoformat()
            ))

        cursor.executemany(
            """INSERT OR IGNORE INTO post_likes VALUES (?, ?, ?, ?)""",
            likes
        )

        self.conn.commit()
        print(f"  ✓ {len(follows)} follows, {len(likes)} likes created")

    def _vllm_batch_titles(self, count: int, batch_size: int = 100):
        """Generate blog post titles from vLLM"""
        results = []

        for batch_start in range(0, count, batch_size):
            batch_count = min(batch_size, count - batch_start)

            try:
                response = self.client.chat.completions.create(
                    model="local",
                    messages=[{
                        "role": "user",
                        "content": f"""Generate {batch_count} unique blog post titles.

Requirements:
- 5-12 words each
- Clickworthy and informative
- Varied topics (technology, culture, lifestyle, productivity)
- Professional tone

Format: One title per line, no numbering"""
                    }],
                    max_tokens=batch_count * 20,
                    temperature=0.7,
                    top_p=0.95
                )

                titles = response.choices[0].message.content.strip().split('\n')
                results.extend([t.strip() for t in titles if t.strip()][:batch_count])

                print(f"    Titles: {min(batch_start + batch_count, count)}/{count}")
            except Exception as e:
                print(f"  ⚠️  vLLM error: {e}. Using fallback titles.")
                results.extend([f"Blog Post {i}" for i in range(batch_count)])

        return results[:count]

    def _vllm_batch_content(self, count: int, batch_size: int = 50):
        """Generate blog post bodies from vLLM"""
        results = []

        for batch_start in range(0, count, batch_size):
            batch_count = min(batch_size, count - batch_start)

            try:
                response = self.client.chat.completions.create(
                    model="local",
                    messages=[{
                        "role": "user",
                        "content": f"""Generate {batch_count} short blog post bodies.

Requirements:
- 300-800 words each
- Structured with 2-3 paragraphs
- Professional, informative tone
- Diverse topics

Separate each post with "---" on its own line."""
                    }],
                    max_tokens=batch_count * 300,
                    temperature=0.7,
                    top_p=0.95
                )

                posts = response.choices[0].message.content.split('---')
                results.extend([p.strip() for p in posts if p.strip()][:batch_count])

                print(f"    Content: {min(batch_start + batch_count, count)}/{count}")
            except Exception as e:
                print(f"  ⚠️  vLLM error: {e}. Using fallback content.")
                results.extend([f"Content for post {i}. " * 50 for i in range(batch_count)])

        return results[:count]

    def _vllm_batch_comments(self, count: int, batch_size: int = 50):
        """Generate comments from vLLM"""
        results = []

        for batch_start in range(0, count, batch_size):
            batch_count = min(batch_size, count - batch_start)

            try:
                response = self.client.chat.completions.create(
                    model="local",
                    messages=[{
                        "role": "user",
                        "content": f"""Generate {batch_count} realistic blog comments.

Requirements:
- 20-100 words each
- Sound like real user comments
- Can be positive, critical, or questioning
- Conversational tone

Format: One comment per line"""
                    }],
                    max_tokens=batch_count * 100,
                    temperature=0.7,
                    top_p=0.95
                )

                comments = response.choices[0].message.content.strip().split('\n')
                results.extend([c.strip() for c in comments if c.strip()][:batch_count])

                print(f"    Comments: {min(batch_start + batch_count, count)}/{count}")
            except Exception as e:
                print(f"  ⚠️  vLLM error: {e}. Using fallback comments.")
                results.extend([f"Comment {i}" for i in range(batch_count)])

        return results[:count]

    def finalize(self):
        """Optimize database"""
        print("Optimizing database...")
        self.conn.execute("VACUUM")
        self.conn.execute("ANALYZE")
        self.conn.close()

        # Show file size
        size_mb = Path(self.db_path).stat().st_size / (1024 * 1024)
        print(f"  ✓ Database optimized: {size_mb:.1f} MB")

    def run(self):
        """Run full generation pipeline"""
        import time
        start = time.time()

        try:
            self.create_schema()
            self.generate_users(500)
            self.generate_posts(5000)
            self.generate_comments(25000)
            self.generate_relationships()
            self.finalize()

            elapsed = time.time() - start
            print(f"\n✅ XS generation complete in {elapsed/60:.1f} minutes")
            return True
        except Exception as e:
            print(f"\n❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "datasets/fraiseql_xs_test.db"

    print(f"Generating XS database: {db_path}")
    print("=" * 60)

    generator = XSGenerator(db_path)
    success = generator.run()

    sys.exit(0 if success else 1)
```

---

## Phase 2: Run Generation (15-20 minutes)

### 2.1 Ensure vLLM is Running

```bash
# Check if vLLM is available
curl http://localhost:8000/v1/models

# If not running, start it (from aoza-project-management backend)
vllm-switch status
vllm-switch implementer  # or your preferred model
```

### 2.2 Run XS Generator

```bash
cd /home/lionel/code/fraiseql-performance-assessment

# Create datasets directory
mkdir -p datasets

# Run generator (15-20 minutes)
python database/xs-generator.py datasets/fraiseql_xs_test.db

# Expected output:
# Creating schema...
# Generating 500 users...
#   ✓ 500 users created
# Generating 5000 posts...
#   Generating titles from vLLM...
#     Titles: 5000/5000
#   Generating content from vLLM...
#     Content: 5000/5000
#   ✓ 5000 posts created
# Generating 25000 comments...
#   Generating comment content from vLLM...
#     Comments: 25000/25000
#   ✓ 25000 comments created
# Generating relationships...
#   ✓ 2500 follows, 10000 likes created
# Optimizing database...
#   ✓ Database optimized: 150-200 MB
#
# ✅ XS generation complete in 15-20 minutes
```

---

## Phase 3: Validate SQLite (2 minutes)

### 3.1 Quick Validation Script

File: `database/validate-xs.py`

```python
#!/usr/bin/env python3
"""Quick validation of XS database"""

import sqlite3
from pathlib import Path

def validate(db_path: str):
    """Validate XS database"""

    conn = sqlite3.connect(db_path)

    checks = {
        'users': (500, "SELECT COUNT(*) FROM users"),
        'posts': (5000, "SELECT COUNT(*) FROM posts"),
        'comments': (25000, "SELECT COUNT(*) FROM comments"),
        'follows': (2000, "SELECT COUNT(*) FROM user_follows"),  # At least
        'likes': (8000, "SELECT COUNT(*) FROM post_likes"),  # At least
    }

    print("Validation Results:")
    print("=" * 60)

    all_pass = True
    for name, (expected, query) in checks.items():
        count = conn.execute(query).fetchone()[0]
        status = "✓" if count >= (expected * 0.9) else "✗"
        print(f"{status} {name:12} {count:,} (expected ~{expected})")
        if count < (expected * 0.9):
            all_pass = False

    # Check referential integrity
    print("\nReferential Integrity:")
    orphan_posts = conn.execute(
        "SELECT COUNT(*) FROM posts WHERE fk_author NOT IN (SELECT pk_user FROM users)"
    ).fetchone()[0]
    orphan_comments = conn.execute(
        "SELECT COUNT(*) FROM comments WHERE fk_post NOT IN (SELECT pk_post FROM posts) OR fk_author NOT IN (SELECT pk_user FROM users)"
    ).fetchone()[0]

    print(f"{'✓' if orphan_posts == 0 else '✗'} Orphaned posts: {orphan_posts}")
    print(f"{'✓' if orphan_comments == 0 else '✗'} Orphaned comments: {orphan_comments}")

    # Sample content
    print("\nSample Content Quality:")
    sample_posts = conn.execute(
        "SELECT title, LENGTH(content) FROM posts ORDER BY RANDOM() LIMIT 3"
    ).fetchall()

    for title, content_len in sample_posts:
        print(f"  • Title: {title} (content: {content_len} chars)")

    sample_comments = conn.execute(
        "SELECT content FROM comments ORDER BY RANDOM() LIMIT 2"
    ).fetchall()

    for (comment,) in sample_comments:
        print(f"  • Comment: {comment[:80]}...")

    conn.close()

    print("\n" + "=" * 60)
    if all_pass and orphan_posts == 0 and orphan_comments == 0:
        print("✅ XS Database validation PASSED")
        return True
    else:
        print("⚠️  XS Database validation has issues")
        return False


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "datasets/fraiseql_xs_test.db"
    validate(db_path)
```

### 3.2 Run Validation

```bash
python database/validate-xs.py datasets/fraiseql_xs_test.db
```

---

## Phase 4: Test PostgreSQL Import (2-3 minutes)

### 4.1 Create Import Script

File: `database/import-xs-to-pg.py`

```python
#!/usr/bin/env python3
"""Import XS SQLite database to PostgreSQL"""

import sqlite3
import psycopg
from psycopg import sql
import sys
from datetime import datetime

def import_xs(sqlite_path: str, pg_conn_str: str):
    """Import XS database from SQLite to PostgreSQL"""

    print(f"Importing {sqlite_path} to PostgreSQL...")
    print("=" * 60)

    sqlite_conn = sqlite3.connect(sqlite_path)
    pg_conn = psycopg.connect(pg_conn_str)

    # Ensure benchmark schema exists
    with pg_conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS benchmark")
    pg_conn.commit()

    tables = [
        ('users', 'tb_user'),
        ('posts', 'tb_post'),
        ('comments', 'tb_comment'),
        ('user_follows', 'tb_user_follows'),
        ('post_likes', 'tb_post_like'),
    ]

    import time
    start = time.time()

    for sqlite_table, pg_table in tables:
        print(f"Importing {sqlite_table}...", end=" ", flush=True)
        table_start = time.time()

        # Get column info from SQLite
        cursor = sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({sqlite_table})")
        columns = [row[1] for row in cursor.fetchall()]

        # Read all data
        cursor.execute(f"SELECT * FROM {sqlite_table}")
        rows = cursor.fetchall()

        # Insert into PostgreSQL
        if rows:
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO benchmark.{pg_table} ({', '.join(columns)}) VALUES ({placeholders})"

            with pg_conn.cursor() as cur:
                for batch_start in range(0, len(rows), 1000):
                    batch = rows[batch_start:batch_start + 1000]
                    cur.executemany(insert_sql, batch)
                pg_conn.commit()

        elapsed = time.time() - table_start
        print(f"✓ {len(rows):,} rows in {elapsed:.1f}s")

    total_elapsed = time.time() - start
    print("=" * 60)
    print(f"✅ Import complete in {total_elapsed:.1f}s")

    sqlite_conn.close()
    pg_conn.close()


if __name__ == "__main__":
    import os

    sqlite_path = sys.argv[1] if len(sys.argv) > 1 else "datasets/fraiseql_xs_test.db"
    pg_conn_str = os.getenv(
        "DATABASE_URL",
        "postgresql://benchmark:benchmark123@localhost:5434/fraiseql_benchmark"
    )

    import_xs(sqlite_path, pg_conn_str)
```

### 4.2 Run Import

```bash
# Start PostgreSQL container if not running
docker-compose up -d postgres

# Wait for it to be ready
sleep 5

# Run import
python database/import-xs-to-pg.py datasets/fraiseql_xs_test.db

# Verify in PostgreSQL
psql postgresql://benchmark:benchmark123@localhost:5434/fraiseql_benchmark -c \
  "SELECT
    (SELECT COUNT(*) FROM benchmark.tb_user) as users,
    (SELECT COUNT(*) FROM benchmark.tb_post) as posts,
    (SELECT COUNT(*) FROM benchmark.tb_comment) as comments"
```

---

## Phase 5: Validation & Timing (2 minutes)

### 5.1 Check Results

```bash
# Verify import succeeded
psql postgresql://benchmark:benchmark123@localhost:5434/fraiseql_benchmark -c \
  "SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE schemaname='benchmark'"

# Sample data
psql postgresql://benchmark:benchmark123@localhost:5434/fraiseql_benchmark -c \
  "SELECT title, LENGTH(content) as content_len FROM benchmark.tb_post LIMIT 5"
```

### 5.2 Measure End-to-End Time

```bash
# Full test timing
time (
  echo "Generation..."
  python database/xs-generator.py datasets/fraiseql_xs_test.db

  echo -e "\nValidation..."
  python database/validate-xs.py datasets/fraiseql_xs_test.db

  echo -e "\nImport..."
  python database/import-xs-to-pg.py datasets/fraiseql_xs_test.db
)
```

---

## Expected Results

✅ **Timing** (all 3 phases):
- Generation: 15-20 minutes
- Validation: 1 minute
- Import to PG: 1-2 minutes
- **Total: ~20-25 minutes**

✅ **Data Quality**:
- 500 users ✓
- 5,000 posts with realistic titles/content ✓
- 25,000 comments with realistic text ✓
- All foreign keys valid ✓
- No orphaned records ✓

✅ **Scaling Inference**:
- XS: 150-200 MB, 20-25 min
- XL: 12-17 GB, 4-5 hours (linear scaling)
- Content generation will be bottleneck (vLLM)

---

## What This Tells Us

If XS test succeeds:
- ✅ vLLM integration works
- ✅ SQLite schema is solid
- ✅ Import process is reliable
- ✅ Scaling calculations are valid
- ✅ Content quality is acceptable

**Next step**: Run full XL generation with confidence (or adjust approach if issues found)

If XS test fails:
- Identify specific failure point
- Fix vLLM prompts, generation logic, or import process
- Retry with confidence
- Scale to XL once validated

---

## Files to Create

1. ✅ `database/schema-sqlite-xs.sql` - Minimal SQLite schema
2. ✅ `database/xs-generator.py` - Quick XS generator (~400 lines)
3. ✅ `database/validate-xs.py` - Validation script (~60 lines)
4. ✅ `database/import-xs-to-pg.py` - Import script (~80 lines)

**Total effort**: ~30 minutes execution, can run while you work on other tasks
