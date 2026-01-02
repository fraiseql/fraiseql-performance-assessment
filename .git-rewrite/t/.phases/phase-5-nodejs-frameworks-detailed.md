# FraiseQL Performance Assessment - Phase 5: Node.js Framework Implementations

## Phase Overview

**Goal**: Implement Apollo Server (GraphQL) and Express (REST) frameworks with production-grade async patterns, connection pooling, and DataLoader for N+1 prevention comparison against Python frameworks.

**Scope**: Add Node.js/JavaScript frameworks to the benchmark suite, implementing equivalent functionality with proper async patterns and performance optimizations.

**Success Criteria**:
- Apollo Server starts and responds to GraphQL queries
- Express REST implements equivalent endpoints
- DataLoader batches related entity lookups
- Connection pools configured (min 10, max 50)
- Health and metrics endpoints functional
- Docker containers build and run successfully

## Learning Objectives

As a junior engineer, by completing Phase 5 you will learn:

1. **Large-Scale Data Generation**: Faker library usage, reproducible seeding, batch processing
2. **Database Performance Tuning**: Index creation, query optimization, EXPLAIN analysis
3. **Data Consistency Management**: TV table synchronization, referential integrity
4. **Production Data Patterns**: Realistic social media data modeling, relationships
5. **Batch Processing**: Efficient bulk inserts, memory management, progress tracking
6. **PostgreSQL Advanced Features**: Generated columns, GIN indexes, full-text search
7. **Testing Data Management**: Parameterized test data, dataset versioning, cleanup

## Prerequisites and Knowledge Requirements

### Required Knowledge
- Basic SQL DDL/DML operations
- Python data generation concepts
- Database indexing principles
- Basic PostgreSQL administration

### Required Tools
- faker library for data generation
- psycopg for database operations
- PostgreSQL with extensions

## Implementation Steps

### Step 1: Scalable Data Generator
**Estimated Time**: 2 hours

**Learning Objective**: Building production-scale data generation systems

```python
# database/seed-generator.py - Key implementation

class DataGenerator:
    def __init__(self, conn_string: str):
        self.conn = psycopg.connect(conn_string)
        # Track generated IDs for relationships
        self.user_ids = []
        self.post_ids = []
    
    def generate_users(self, count: int):
        """Generate users with batch processing"""
        print(f"Generating {count} users...")
        
        with self.conn.cursor() as cur:
            for batch_start in range(0, count, 1000):
                batch_end = min(batch_start + 1000, count)
                users_data = []
                
                for i in range(batch_start, batch_end):
                    # Predictable IDs for first 100 users (testing)
                    user_id = uuid.uuid4() if i >= 100 else uuid.UUID(f"{i+1:08d}-1111-1111-1111-111111111111")
                    self.user_ids.append(user_id)
                    
                    users_data.append((
                        user_id,
                        fake.email(),
                        fake.user_name()[:100],
                        fake.first_name(),
                        fake.last_name(),
                        fake.text(500) if random.random() > 0.3 else None
                    ))
                
                # Batch insert
                cur.executemany("""
                    INSERT INTO benchmark.users (id, email, username, first_name, last_name, bio)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, users_data)
                
                print(f"  Users: {batch_end}/{count}")
        
        self.conn.commit()
    
    def generate_relationships(self):
        """Generate social relationships"""
        print("Generating social relationships...")
        
        with self.conn.cursor() as cur:
            # Generate follows (5 per user average)
            follows = []
            for user_id in self.user_ids:
                # Each user follows ~5 random users
                follow_targets = random.sample(
                    [u for u in self.user_ids if u != user_id], 
                    min(5, len(self.user_ids) - 1)
                )
                
                for target_id in follow_targets:
                    follows.append((user_id, target_id))
            
            # Batch insert follows
            cur.executemany("""
                INSERT INTO benchmark.user_follows (follower_id, following_id)
                VALUES (%s, %s)
            """, follows)
            
            # Generate likes (2 per post average)
            likes = []
            for post_id in self.post_ids:
                # Random users like each post
                likers = random.sample(self.user_ids, min(2, len(self.user_ids)))
                reaction_types = ['like'] * 7 + ['love'] * 2 + ['laugh'] * 1
                
                for liker_id in likers:
                    likes.append((liker_id, post_id, random.choice(reaction_types)))
            
            cur.executemany("""
                INSERT INTO benchmark.post_likes (user_id, post_id, reaction_type)
                VALUES (%s, %s, %s)
            """, likes)
        
        self.conn.commit()

# Configuration presets
PRESETS = {
    "large": {"users": 10000, "posts": 100000, "comments": 500000, "follows": 50000, "likes": 200000}
}
```

### Step 2: Index Optimization
**Estimated Time**: 1 hour

**Learning Objective**: Database index design and performance optimization

```sql
-- database/05-fulltext-indexes.sql

-- Full-text search setup
ALTER TABLE benchmark.posts ADD COLUMN IF NOT EXISTS search_vector tsvector;
ALTER TABLE benchmark.users ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Populate search vectors
UPDATE benchmark.posts SET search_vector = 
    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(content, '')), 'B');

UPDATE benchmark.users SET search_vector = 
    setweight(to_tsvector('english', COALESCE(username, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(first_name || ' ' || last_name, '')), 'B');

-- Create GIN indexes for full-text search
CREATE INDEX idx_posts_search ON benchmark.posts USING GIN (search_vector);
CREATE INDEX idx_users_search ON benchmark.users USING GIN (search_vector);

-- Performance indexes
CREATE INDEX idx_posts_author_status ON benchmark.posts (author_id, status);
CREATE INDEX idx_posts_created_at ON benchmark.posts (created_at DESC);
CREATE INDEX idx_comments_post_approved ON benchmark.comments (post_id, is_approved);
CREATE INDEX idx_user_follows_following ON benchmark.user_follows (following_id);
CREATE INDEX idx_post_likes_post ON benchmark.post_likes (post_id);
```

### Step 3: JMeter Dataset Generation
**Estimated Time**: 45 minutes

**Learning Objective**: Test data management for load testing

```bash
# tests/perf/datasets/generate-datasets.sh

#!/bin/bash
DB_CONN="postgresql://benchmark:benchmark123@localhost:5434/fraiseql_benchmark"

# Generate parameterized datasets
psql "$DB_CONN" -t -A -c "
SELECT id FROM benchmark.users ORDER BY random() LIMIT 1000
" > tests/perf/datasets/user_ids.csv

psql "$DB_CONN" -t -A -c "
SELECT id FROM benchmark.posts WHERE status = 'published' ORDER BY random() LIMIT 1000
" > tests/perf/datasets/post_ids.csv

# Generate search terms from actual content
psql "$DB_CONN" -t -A -c "
SELECT word FROM (
    SELECT unnest(tsvector_to_array(search_vector)) as word
    FROM benchmark.posts
    WHERE search_vector @@ to_tsquery('english', 'a')
    LIMIT 100
) t GROUP BY word ORDER BY random() LIMIT 50
" > tests/perf/datasets/search_terms.csv
```

## Testing Strategy

### Data Validation
- Row count verification against expected volumes
- Referential integrity checks
- Index usage validation with EXPLAIN
- Search functionality testing

### Performance Validation
- Query execution time comparison (small vs large dataset)
- Index effectiveness verification
- Memory usage monitoring during queries

## Best Practices Learned

### 1. Data Generation
- Use seeded random generation for reproducibility
- Implement batch processing for large datasets
- Validate data integrity during generation
- Document data patterns and relationships

### 2. Index Design
- Create indexes for common query patterns
- Use appropriate index types (B-tree, GIN, etc.)
- Monitor index usage and effectiveness
- Balance index benefits vs write performance

### 3. Performance Testing
- Test with production-scale data volumes
- Validate query plans use appropriate indexes
- Monitor system resource usage under load
- Establish performance baselines

## Phase Sign-off

**Phase 4 Status**: ☐ Ready for Phase 5 ☐ Needs Remediation

**Dataset Statistics**:
- Users: 10,000+
- Posts: 100,000+
- Comments: 500,000+
- Database size: 200MB+

**Performance Validations**:
- Indexes used in query plans
- Full-text search operational
- Data generation reproducible</content>
<parameter name="filePath">.phases/phase-4-data-volume-scaling-detailed.md