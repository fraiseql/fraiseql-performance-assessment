# XLarge Dataset with Git LFS + vLLM Content Generation
## Comprehensive Implementation Plan

**Objective**: Generate and maintain a 12-17GB SQLite database with XLarge benchmark data (100K users, 1M posts, 5M comments) using Git LFS for storage and vLLM for realistic content generation.

**Timeline**: ~3 weeks (generation is a one-time cost)

---

## PHASE 1: Planning & Setup (Days 1-2)

### 1.1 Architectural Decisions

**Hybrid Generation Strategy**:
```
├─ Faker (Structured Data)
│  ├─ Users: names, emails, usernames, timestamps
│  ├─ Posts: dates, author relationships, published status
│  ├─ Comments: threads, dates, author relationships
│  └─ Follows/Likes: relationships
│
└─ vLLM (Content Data)
   ├─ Post titles: realistic blog titles (~50-100 words)
   ├─ Post content: realistic blog posts (~1-2KB each)
   └─ Comment text: realistic comments (~100-300 words each)
```

**Why split?**
- Faker excels at generating structured data, UUIDs, timestamps, relationships
- vLLM excels at generating realistic, contextually-aware text
- Separates concerns: schema/structure vs content quality
- Faster generation: batch Faker operations then batch vLLM for content

### 1.2 Git LFS Configuration

**Track SQLite files**:
```bash
git lfs install
git lfs track "datasets/*.db"
```

**Storage considerations**:
- SQLite file size: 12-17 GB
- Git LFS free tier: 1 GB/month (need paid account for continuous use)
- Alternative: Generate on GitHub Actions for benchmarks only
- Local workflow: Download once, reuse across test runs

### 1.3 Data Volume (100K users, 1M posts, 5M comments)

**Why XLarge?**
- 100K users = realistic mid-size platform (scale issues visible)
- 1M posts = performance differences emerge
- 5M comments = N+1 problems become severe
- 12-17GB SQLite = meaningful for disk I/O benchmarking
- 2-3 hour PostgreSQL import = realistic benchmark setup time

---

## PHASE 2: SQLite Schema & Generation Framework (Days 3-5)

### 2.1 Create SQLite Schema

**File**: `database/schema-sqlite.sql`

Structure mirrors PostgreSQL but optimized for generation:
```sql
-- SQLite pragmas for faster bulk inserts
PRAGMA journal_mode = MEMORY;
PRAGMA synchronous = OFF;
PRAGMA cache_size = 1000000;
PRAGMA temp_store = MEMORY;

-- Tables (identical to PostgreSQL structure)
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

-- Similar for comments, follows, likes...
```

**Why SQLite for generation?**
- Fast insertion with PRAGMA settings
- No network overhead (vs PostgreSQL)
- Portable: can be distributed via git-lfs
- Reproducible: same SQLite file = exact same data every import

### 2.2 Create Enhanced Seed Generator

**File**: `database/xlarge-generator.py`

**Structure**:
```python
class XLargeGenerator:
    """Generate XLarge dataset combining Faker + vLLM"""

    def __init__(self, sqlite_path: str, vllm_endpoint: str = "http://localhost:8000"):
        self.conn = sqlite3.connect(sqlite_path)
        self.vllm = VLLMContentGenerator(vllm_endpoint)

    def generate_all(self):
        """Phase 1-3 pipeline"""
        self.phase1_users()        # Faker: 100K users
        self.phase2_posts()        # Faker structure + vLLM content
        self.phase3_comments()     # Faker structure + vLLM content
        self.phase4_relationships() # Faker: follows, likes
        self.finalize()            # Indexes, vacuum
```

**Two-phase content generation loop**:

**Phase A: Generate Structure (Faker)**
```python
def phase2_posts(self):
    """Generate 1M posts with structure from Faker, content from vLLM"""

    for batch_start in range(0, 1000000, 10000):
        # Step 1: Generate structure with Faker (fast)
        posts_structure = []
        for i in range(batch_start, min(batch_start + 10000, 1000000)):
            posts_structure.append({
                'id': str(uuid.uuid4()),
                'identifier': self.fake.slug()[:50],
                'fk_author': random.randint(1, 100000),
                'published': random.random() > 0.2,
                'created_at': self.fake.date_time_this_year(),
            })

        # Step 2: Batch generate content with vLLM (moderate cost)
        titles = self.vllm.batch_generate_titles(
            count=10000,
            style="blog_post_title",
            batch_size=100
        )

        content = self.vllm.batch_generate_content(
            count=10000,
            style="blog_post_body",
            batch_size=100
        )

        # Step 3: Combine and insert
        for i, post in enumerate(posts_structure):
            post['title'] = titles[i]
            post['content'] = content[i]

        self._bulk_insert_posts(posts_structure)
        print(f"Posts: {min(batch_start + 10000, 1000000)}/1000000")
```

### 2.3 vLLM Content Generator Module

**File**: `database/vllm_content_gen.py`

```python
class VLLMContentGenerator:
    """Generate realistic blog content using vLLM"""

    def __init__(self, endpoint: str = "http://localhost:8000/v1"):
        self.endpoint = endpoint
        self.client = OpenAI(api_key="none", base_url=endpoint)

    def batch_generate_titles(self, count: int, style: str = "blog_post_title", batch_size: int = 50):
        """Generate batch of realistic post titles"""

        prompt = f"""Generate {batch_size} unique, realistic blog post titles.
        Style: {style}
        Titles should be:
        - 5-12 words
        - Click-worthy but informative
        - Varied topics (tech, culture, lifestyle, productivity)

        Format: One title per line, no numbering
        """

        results = []
        for batch_start in range(0, count, batch_size):
            response = self.client.chat.completions.create(
                model="local",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=batch_size * 20,
                temperature=0.7,
                top_p=0.95
            )

            titles = response.choices[0].message.content.strip().split('\n')
            results.extend([t.strip() for t in titles if t.strip()][:batch_size])

        return results[:count]

    def batch_generate_content(self, count: int, style: str = "blog_post_body", batch_size: int = 20):
        """Generate batch of blog post bodies"""

        prompt = f"""Generate {batch_size} realistic blog post bodies.

        Requirements:
        - 500-2500 words each (simulate realistic blog length)
        - Structured with paragraphs
        - Include headers/sections if natural
        - Diverse topics but professional tone

        Separate posts with "---" on its own line.
        """

        results = []
        for batch_start in range(0, count, batch_size):
            response = self.client.chat.completions.create(
                model="local",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=batch_size * 500,  # 500 tokens per post estimate
                temperature=0.7,
                top_p=0.95
            )

            posts = response.choices[0].message.content.split('---')
            results.extend([p.strip() for p in posts if p.strip()][:batch_size])

        return results[:count]
```

---

## PHASE 3: Generation Execution (Days 6-9)

### 3.1 Generate SQLite Database

**Process**:
```bash
# 1. Ensure vLLM is running
# 2. Run generator
python database/xlarge-generator.py \
  --output datasets/fraiseql_benchmark_xlarge.db \
  --users 100000 \
  --posts 1000000 \
  --comments 5000000 \
  --batch-size 10000

# Estimated time breakdown:
# - Users + Structure (Faker): ~20 minutes
# - Post content (vLLM): ~90 minutes (100 batch generations @ ~1 min each)
# - Comment content (vLLM): ~120 minutes (250 batch generations)
# - Relationships (Faker): ~10 minutes
# - Indexing + Optimization: ~20 minutes
# ────────────────────────────────────
# TOTAL: ~4-5 hours
```

**Monitoring**:
```bash
# In separate terminal
watch -n 10 'ls -lh datasets/fraiseql_benchmark_xlarge.db'

# Check SQLite size growth
sqlite3 datasets/fraiseql_benchmark_xlarge.db "SELECT page_count * page_size / (1024*1024) AS size_mb FROM pragma_page_count(), pragma_page_size();"
```

### 3.2 Quality Validation

**Script**: `database/validate-xlarge.py`

```python
def validate_dataset():
    """Verify data integrity and relationships"""

    checks = {
        'user_count': lambda: count_rows('users'),  # Expect 100K
        'post_count': lambda: count_rows('posts'),  # Expect 1M
        'comment_count': lambda: count_rows('comments'),  # Expect 5M
        'fk_integrity': lambda: check_foreign_keys(),
        'no_orphans': lambda: verify_no_orphaned_records(),
        'content_quality': lambda: sample_and_inspect_content(sample_size=100),
    }

    for check_name, check_fn in checks.items():
        result = check_fn()
        print(f"✓ {check_name}: {result}")
```

**Expected checks**:
- ✅ 100K users exist
- ✅ 1M posts reference valid user IDs
- ✅ 5M comments reference valid post/user IDs
- ✅ No orphaned records
- ✅ Post content is diverse and realistic (sample 100)
- ✅ Comment content is realistic
- ✅ Timestamps are properly distributed

---

## PHASE 4: Git LFS Integration (Days 10-11)

### 4.1 Setup Git LFS

```bash
# 1. Install git-lfs (if not present)
# macOS: brew install git-lfs
# Ubuntu: sudo apt-get install git-lfs
# Fedora: sudo dnf install git-lfs

# 2. Initialize in repo
cd /home/lionel/code/fraiseql-performance-assessment
git lfs install

# 3. Track SQLite files
git lfs track "datasets/*.db"
git add .gitattributes
git commit -m "chore: configure git-lfs for SQLite datasets"

# 4. Add the generated database
git add datasets/fraiseql_benchmark_xlarge.db
git commit -m "data: add xlarge benchmark dataset (100K users, 1M posts, 5M comments)"

# 5. Push (first time will upload to lfs storage)
git push origin main
```

### 4.2 Update .gitattributes

**File**: `.gitattributes` (create if doesn't exist)

```
# Git LFS - SQLite Databases
*.db filter=lfs diff=lfs merge=lfs -text
datasets/*.db filter=lfs diff=lfs merge=lfs -text

# Also exclude from normal git
*.db binary
```

### 4.3 Storage Strategy

**Three options** (choose one):

**Option A: GitHub LFS (Recommended for teams)**
- Cost: $5/month for 100GB storage + 100GB/month bandwidth
- Benefit: Seamless, CI/CD auto-downloads
- Setup: Enable in GitHub repo settings
- Clone speed: ~2-3 minutes for 17GB over network

**Option B: Generate on CI (Recommended for cost)**
- Cost: Free (uses CI compute time)
- Benefit: No storage cost, always fresh data
- Trade-off: Benchmark runs take 5+ hours (generation + import)
- Best for: Nightly/weekly benchmarks, not per-commit

**Option C: Local storage only (for development)**
- Cost: Local disk space (20GB storage)
- Benefit: Fastest local tests
- Trade-off: Not in git, manual synchronization
- Add to .gitignore: `datasets/*.db` (exclude from git)

**Recommended**: **Option B + small Option C**
- Store small fixture (500MB) in git-lfs for quick local tests
- Generate xlarge on-demand in CI for full benchmarks
- Fallback to Option A if CI time becomes limiting

---

## PHASE 5: Import & Integration (Days 12-14)

### 5.1 Create SQLite → PostgreSQL Import Script

**File**: `database/import-from-sqlite.py`

```python
#!/usr/bin/env python3
"""Import data from SQLite database to PostgreSQL"""

import sqlite3
import psycopg
from pathlib import Path

def import_from_sqlite(sqlite_path: str, pg_conn_str: str):
    """Bulk import SQLite database to PostgreSQL"""

    sqlite_conn = sqlite3.connect(sqlite_path)
    pg_conn = psycopg.connect(pg_conn_str)

    tables = [
        'users',        # 100K rows
        'posts',        # 1M rows
        'comments',     # 5M rows
        'user_follows', # 500K rows
        'post_likes',   # 2M rows
    ]

    for table in tables:
        print(f"Importing {table}...")

        # Read from SQLite
        cursor = sqlite_conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()

        # Batch insert into PostgreSQL
        with pg_conn.cursor() as cur:
            for batch in batched(rows, 10000):
                placeholders = ', '.join(['%s'] * len(batch[0]))
                sql = f"INSERT INTO {table} VALUES ({placeholders})"
                cur.executemany(sql, batch)
            pg_conn.commit()

        print(f"  ✓ {len(rows)} rows")

    pg_conn.close()
    sqlite_conn.close()

# Usage
if __name__ == "__main__":
    import_from_sqlite(
        sqlite_path="datasets/fraiseql_benchmark_xlarge.db",
        pg_conn_str="postgresql://benchmark:benchmark123@localhost/fraiseql_benchmark"
    )
```

**Performance targets**:
- 100K users: ~30 seconds
- 1M posts: ~2 minutes
- 5M comments: ~5 minutes
- 500K follows: ~1 minute
- 2M likes: ~2 minutes
- **Total**: ~10-15 minutes per import

### 5.2 Docker Integration

**Update**: `docker-compose.yml`

```yaml
services:
  postgres:
    # ... existing config ...
    environment:
      DATA_VOLUME: ${DATA_VOLUME:-small}  # small, medium, large, xlarge
    volumes:
      # SQLite source (when DATA_VOLUME=xlarge)
      - ./datasets/fraiseql_benchmark_xlarge.db:/sqlite/data.db:ro
      # Import script
      - ./database/import-from-sqlite.py:/docker-entrypoint-initdb.d/99-import-sqlite.py
      # Conditional import setup script
      - ./database/docker-import-entrypoint.sh:/docker-entrypoint-initdb.d/00-setup-import.sh
```

**Setup script**: `database/docker-import-entrypoint.sh`

```bash
#!/bin/bash
set -e

if [ "$DATA_VOLUME" = "xlarge" ]; then
    echo "DATA_VOLUME=xlarge: Importing from SQLite..."

    # Wait for PostgreSQL to be ready
    until PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1" > /dev/null 2>&1; do
        echo "Waiting for PostgreSQL..."
        sleep 2
    done

    # Run import
    python3 /docker-entrypoint-initdb.d/99-import-sqlite.py

    echo "SQLite import complete!"
fi
```

### 5.3 Manual Import for Development

```bash
# Start PostgreSQL in Docker
docker-compose up -d postgres

# Wait for it to be ready
sleep 10

# Run import
python database/import-from-sqlite.py \
  --sqlite datasets/fraiseql_benchmark_xlarge.db \
  --db postgresql://benchmark:benchmark123@localhost:5434/fraiseql_benchmark
```

---

## PHASE 6: CI/CD & Testing (Days 15-17)

### 6.1 Add Benchmark Workflow

**File**: `.github/workflows/xlarge-benchmark.yml`

```yaml
name: XLarge Benchmark Generation

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly, Sunday 2 AM UTC
  workflow_dispatch:

jobs:
  generate-xlarge:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true  # Auto-download LFS files

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install faker psycopg[binary] requests

      - name: Generate XLarge dataset
        run: |
          python database/xlarge-generator.py \
            --output datasets/fraiseql_benchmark_xlarge.db \
            --users 100000 \
            --posts 1000000 \
            --comments 5000000 \
            --vllm-endpoint "http://vllm-server:8000/v1"
        timeout-minutes: 360  # 6 hours

      - name: Upload to LFS
        run: |
          git add datasets/fraiseql_benchmark_xlarge.db
          git commit -m "data: regenerate xlarge dataset"
          git push
```

### 6.2 Add Benchmark Testing Job

**File**: `.github/workflows/benchmark-xlarge.yml`

```yaml
name: Run XLarge Benchmarks

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 8 * * 0'  # Weekly, Sunday 8 AM UTC (after generation)

jobs:
  benchmark:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: fraiseql_benchmark
          POSTGRES_USER: benchmark
          POSTGRES_PASSWORD: benchmark123
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true  # Download SQLite from LFS

      - name: Import XLarge dataset
        run: |
          pip install psycopg[binary]
          python database/import-from-sqlite.py \
            --sqlite datasets/fraiseql_benchmark_xlarge.db \
            --db postgresql://benchmark:benchmark123@postgres/fraiseql_benchmark
        timeout-minutes: 30

      - name: Run benchmark suite
        run: |
          docker-compose -f docker-compose.yml up -d

          # Wait for all services
          sleep 120

          # Run actual benchmarks (using jmeter, k6, or custom suite)
          python tests/perf/run-all-benchmarks.py

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results-xlarge
          path: tests/perf/results/
```

---

## PHASE 7: Monitoring & Iteration (Days 18-21)

### 7.1 Content Quality Monitoring

**Script**: `database/monitor-content-quality.py`

```python
def monitor_content_quality(db_path: str):
    """Sample content and verify quality metrics"""

    conn = sqlite3.connect(db_path)

    # Sample 100 posts
    posts = conn.execute(
        "SELECT title, content FROM posts ORDER BY RANDOM() LIMIT 100"
    ).fetchall()

    metrics = {
        'avg_title_length': np.mean([len(p[0]) for p in posts]),
        'avg_content_length': np.mean([len(p[1]) for p in posts]),
        'unique_words': len(set(
            ' '.join([p[0] + p[1] for p in posts]).split()
        )),
        'readability_grade': compute_flesch_kincaid(posts),
    }

    print("Content Quality Report:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value}")
```

**Expected metrics**:
- Avg title length: 50-100 characters ✅
- Avg content length: 1000-2500 characters ✅
- Unique vocabulary: 50K+ distinct words ✅
- Flesch-Kincaid grade: 8-12 (college level) ✅

### 7.2 Import Performance Tracking

```bash
# Measure import time
time python database/import-from-sqlite.py

# Track PostgreSQL size
psql -c "SELECT pg_size_pretty(pg_database_size('fraiseql_benchmark'));"

# Verify record counts
psql -c "SELECT
  (SELECT count(*) FROM benchmark.tb_user) as users,
  (SELECT count(*) FROM benchmark.tb_post) as posts,
  (SELECT count(*) FROM benchmark.tb_comment) as comments;"
```

### 7.3 Iterate Based on Results

If performance issues arise:

**Slow generation**:
- Increase vLLM batch size (trades latency for throughput)
- Reduce content length targets
- Parallelize content generation across multiple vLLM instances

**Poor content quality**:
- Refine prompts for more diverse/realistic text
- Increase temperature/top-p for more variation
- Add domain-specific prompt templates (tech topics, lifestyle, etc.)

**Slow imports**:
- Increase PostgreSQL batch size
- Use `UNLOGGED TABLES` during import
- Disable indexes until after import, then rebuild

---

## Key Architectural Decisions

### ✅ Decision: Hybrid Faker + vLLM

| Aspect | Faker | vLLM | Hybrid ✅ |
|--------|-------|------|---------|
| **Structured data** | ⭐⭐⭐ | ⭐ | Use Faker |
| **Realistic content** | ⭐ | ⭐⭐⭐ | Use vLLM |
| **Generation speed** | Fast | Moderate | Balanced |
| **Data diversity** | High | Very high | Maximum |
| **Cost** | Free | Free (local) | Free |
| **Implementation** | Simple | Complex | Manageable |

### ✅ Decision: SQLite Intermediary

| Aspect | Pros | Cons |
|--------|------|------|
| **Portability** | One file, easy to share | Single point of failure |
| **Generation** | No schema conflicts | SQLite peculiarities |
| **Distribution** | Via Git-LFS | Large file overhead |
| **Testing** | Can run locally offline | Needs network for LFS |

### ✅ Decision: Git-LFS for Storage

| Approach | Storage | Bandwidth | Cost | CI Complexity |
|----------|---------|-----------|------|---------------|
| **Git-LFS paid** | Unlimited | 100GB/month | $5/month | Low |
| **Generate on-demand** | Free | Free | Free | High |
| **Hybrid (Rec.)** | Minimal | Minimal | Free | Medium |

**Hybrid approach**:
- Small fixture (500MB): tracked in git-lfs
- XLarge: generated on-demand in CI
- Development: use small fixture, opt-in for xlarge

---

## Success Criteria

✅ **Data Generation**:
- 100K users generated with diverse profiles
- 1M posts with realistic blog titles (10-15 words)
- 5M comments with varied, realistic content
- Generation completes in <5 hours

✅ **SQLite Database**:
- File size: 12-17 GB
- All foreign key relationships valid
- No orphaned records
- VACUUM optimized

✅ **Git Integration**:
- SQLite file tracked in git-lfs
- Clone with `git clone --depth=1` works
- CI automatically downloads for benchmarks

✅ **PostgreSQL Import**:
- Import from SQLite to PostgreSQL in <15 minutes
- All 6.7M records successfully imported
- Indexes built and optimized

✅ **Benchmark Results**:
- Query performance differences now visible between frameworks
- N+1 problems manifest in slow results
- CQRS sync overhead measurable
- Results statistically significant

---

## Files to Create/Modify

| File | Phase | Status |
|------|-------|--------|
| `database/schema-sqlite.sql` | 2 | ➡️ To create |
| `database/xlarge-generator.py` | 2-3 | ➡️ To create |
| `database/vllm_content_gen.py` | 2-3 | ➡️ To create |
| `database/validate-xlarge.py` | 3 | ➡️ To create |
| `.gitattributes` | 4 | ➡️ To create |
| `database/import-from-sqlite.py` | 5 | ➡️ To create |
| `database/docker-import-entrypoint.sh` | 5 | ➡️ To create |
| `docker-compose.yml` | 5 | ➡️ Modify |
| `.github/workflows/xlarge-benchmark.yml` | 6 | ➡️ To create |
| `.github/workflows/benchmark-xlarge.yml` | 6 | ➡️ To create |
| `database/monitor-content-quality.py` | 7 | ➡️ To create |

---

## Known Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **vLLM unavailable** | Can't generate content | Fallback: use templated content |
| **SQLite file corruption** | Full regeneration needed | Weekly integrity checks |
| **Git-LFS quota exceeded** | Can't push updates | Use generate-on-demand for CI |
| **Import time exceeds CI limits** | Benchmarks don't run | Use parallel import workers |
| **Content quality issues** | Benchmarks don't reflect reality | Sample validation + prompt iteration |

---

## Next Steps

1. **Get approval** on this plan (architecture + timelines)
2. **Phase 2**: Start with SQLite schema and Faker integration
3. **Phase 3**: Implement vLLM content generation
4. **Phase 4**: Generate XLarge dataset (5-6 hours)
5. **Phase 5**: Integrate with Docker and PostgreSQL
6. **Phase 6**: Set up CI/CD workflows
7. **Phase 7**: Monitor quality and iterate
