# Phase Plan: Comprehensive Framework QA Verification

## Objective

Create and execute a comprehensive Quality Assurance verification system that validates all 23 framework implementations across multiple dimensions to ensure fair, accurate, and reliable performance benchmarking.

## Context

The FraiseQL performance assessment project contains 23 framework implementations across 8 programming languages (Python, Node.js, Go, Rust, PHP, Ruby, C#, Java). Initial code review revealed critical issues:

1. **Broken implementation**: async-graphql (Rust) has only TODO placeholders - completely non-functional
2. **Schema inconsistencies**: Different frameworks reference different table names (tv_user vs tb_user vs users)
3. **Varying DataLoader implementations**: Inconsistent limits and batching strategies
4. **Unknown N+1 query status**: Some frameworks haven't been verified for N+1 prevention
5. **Connection pool variations**: Different pool sizes, caching strategies across implementations

This phase will create automated verification tools and manual checklists to validate every framework before benchmarking.

## Files to Create

### Test Infrastructure
- `tests/qa/framework_validator.py` - Main validation orchestrator
- `tests/qa/schema_validator.py` - Database schema consistency checker
- `tests/qa/query_validator.py` - GraphQL/REST query correctness validator
- `tests/qa/n1_detector.py` - N+1 query detection tool
- `tests/qa/data_consistency_validator.py` - Response data consistency checker
- `tests/qa/config_validator.py` - Connection pool and config validator
- `tests/qa/performance_validator.py` - Basic performance sanity checks

### Test Data & Fixtures
- `tests/qa/fixtures/test_queries.json` - Standard test queries for all frameworks
- `tests/qa/fixtures/expected_responses.json` - Expected response shapes
- `tests/qa/fixtures/test_mutations.json` - Standard mutations to test

### Configuration
- `tests/qa/framework_registry.yaml` - Registry of all frameworks with metadata
- `tests/qa/validation_config.yaml` - Validation rules and thresholds

### Documentation
- `tests/qa/README.md` - QA system documentation
- `tests/qa/VALIDATION_REPORT.md` - Template for validation reports
- `.phases/qa-framework-verification/VERIFICATION_RESULTS.md` - Final results (generated)

## Implementation Steps

### Step 1: Create Framework Registry

**File**: `tests/qa/framework_registry.yaml`

Create comprehensive registry with all framework metadata:

```yaml
frameworks:
  # Python GraphQL
  - name: fraiseql
    language: python
    type: graphql
    port: 4000
    endpoint: /graphql
    health_check: /health
    metrics_endpoint: /metrics
    expected_tables:
      - benchmark.tv_user
      - benchmark.tv_post
      - benchmark.tv_comment
    pool_config:
      min: 20
      max: 30
    features:
      - dataloader: native
      - statement_caching: true
      - metrics: prometheus

  - name: strawberry
    language: python
    type: graphql
    port: 8001
    endpoint: /graphql
    health_check: /health
    expected_tables:
      - benchmark.tv_user
      - benchmark.tv_post
      - benchmark.tv_comment
    pool_config:
      min: 10
      max: 50
    features:
      - dataloader: strawberry.DataLoader
      - statement_caching: true
      - dataloaders_count: 4

  # ... (continue for all 23 frameworks)

  - name: async-graphql
    language: rust
    type: graphql
    port: 8000
    endpoint: /graphql
    status: broken  # Mark known issues
    known_issues:
      - "All resolvers return empty TODO implementations"
      - "No database queries implemented"
```

**Acceptance Criteria**:
- [ ] All 23 frameworks registered
- [ ] Each framework has: name, language, type, port, endpoint, expected_tables, pool_config
- [ ] Known issues documented for broken frameworks
- [ ] Feature flags for DataLoader, caching, metrics

### Step 2: Create Schema Validator

**File**: `tests/qa/schema_validator.py`

```python
"""
Schema Validator - Verifies database schema consistency

Tests:
1. All expected tables exist in database
2. Tables have correct columns (id, created_at, updated_at, etc.)
3. Foreign key relationships are correct
4. Indexes exist on foreign keys and frequently queried columns

Outputs:
- List of missing tables
- List of missing columns
- List of missing indexes
- Schema diff report
"""

import asyncpg
from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class TableSchema:
    schema: str
    table: str
    columns: List[str]
    indexes: List[str]
    foreign_keys: List[Dict[str, str]]

class SchemaValidator:
    """Validates database schema matches expected structure."""

    async def connect(self, db_url: str):
        """Connect to database."""
        pass

    async def get_actual_tables(self) -> List[str]:
        """Query pg_catalog to get all tables in benchmark schema."""
        query = """
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE schemaname = 'benchmark'
            ORDER BY tablename
        """
        # Return list of 'schema.table' strings
        pass

    async def get_table_columns(self, schema: str, table: str) -> List[str]:
        """Get all columns for a table."""
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """
        pass

    async def get_table_indexes(self, schema: str, table: str) -> List[str]:
        """Get all indexes for a table."""
        query = """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = $1 AND tablename = $2
        """
        pass

    async def verify_framework_schema(self, framework: Dict) -> Dict:
        """
        Verify a framework references correct tables.

        Returns:
            {
                'framework': 'fraiseql',
                'status': 'pass' | 'fail',
                'missing_tables': [],
                'extra_tables': [],
                'issues': []
            }
        """
        pass

    async def generate_schema_report(self) -> str:
        """Generate markdown report of actual database schema."""
        pass

# Verification Tests:
# - Does benchmark.tv_user exist?
# - Does benchmark.tv_post exist?
# - Does benchmark.tv_comment exist?
# - Does benchmark.tv_user_follows exist? (for follower count queries)
# - Are there tb_user / tb_post / tb_comment tables? (alternate naming)
# - Are there users / posts / comments tables? (FastAPI references these)
```

**Acceptance Criteria**:
- [ ] Connects to PostgreSQL database
- [ ] Enumerates all tables in benchmark schema
- [ ] Detects missing tables referenced by frameworks
- [ ] Detects extra table references not in actual schema
- [ ] Generates schema documentation in markdown
- [ ] Returns pass/fail for each framework

### Step 3: Create Query Validator

**File**: `tests/qa/query_validator.py`

```python
"""
Query Validator - Verifies GraphQL/REST queries return correct data

Tests:
1. All required queries are supported (ping, user, users, post, posts, etc.)
2. Queries return correct data shape
3. Relationships are resolved correctly (user.posts, post.author, etc.)
4. Mutations work and return updated data
5. Error handling works (invalid IDs, missing data)

Outputs:
- Query support matrix (which queries each framework supports)
- Data shape validation results
- Relationship resolution test results
"""

import httpx
import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class QueryTest:
    name: str
    query_type: str  # 'graphql' | 'rest'
    query: str  # GraphQL query or REST path
    variables: Dict[str, Any]
    expected_fields: List[str]
    expected_relationships: List[str]

class QueryValidator:
    """Validates framework query implementations."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_graphql_query(
        self,
        endpoint: str,
        query: str,
        variables: Dict = None
    ) -> Dict:
        """
        Execute GraphQL query and validate response.

        Returns:
            {
                'success': bool,
                'data': dict,
                'errors': list,
                'latency_ms': float
            }
        """
        pass

    async def test_rest_query(
        self,
        endpoint: str,
        path: str,
        params: Dict = None
    ) -> Dict:
        """Execute REST query and validate response."""
        pass

    async def verify_query_support(self, framework: Dict) -> Dict:
        """
        Test all standard queries against framework.

        Tests:
        - ping query
        - user(id: "...") query
        - users(limit: 10) query
        - user { posts { title } } nested query
        - post { author { username } } nested query
        - post { comments { author { username } } } deep nested query

        Returns:
            {
                'framework': 'fraiseql',
                'supported_queries': {
                    'ping': 'pass',
                    'user': 'pass',
                    'users': 'pass',
                    'user_with_posts': 'fail',  # if not working
                    ...
                },
                'issues': []
            }
        """
        pass

    async def verify_data_shape(
        self,
        framework: Dict,
        query_name: str,
        response_data: Any
    ) -> Dict:
        """
        Verify response has correct shape.

        Checks:
        - User has: id, username, first_name, last_name, bio
        - Post has: id, title, content, author
        - Comment has: id, content, author, post
        """
        pass

# Standard test queries to run against all frameworks:
STANDARD_QUERIES = {
    'ping': {
        'query': 'query { ping }',
        'expected': {'ping': 'pong'}
    },
    'user': {
        'query': '''
            query($id: ID!) {
                user(id: $id) {
                    id
                    username
                    firstName
                    lastName
                    bio
                }
            }
        ''',
        'variables': {'id': 'test-user-1'},  # Need actual test data
        'expected_fields': ['id', 'username']
    },
    'user_with_posts': {
        'query': '''
            query($id: ID!) {
                user(id: $id) {
                    id
                    username
                    posts(limit: 5) {
                        id
                        title
                        content
                    }
                }
            }
        ''',
        'expected_relationships': ['posts']
    },
    # ... continue for all queries
}
```

**Acceptance Criteria**:
- [ ] Tests all standard queries (ping, user, users, post, posts, comment)
- [ ] Tests nested queries (user.posts, post.author, post.comments)
- [ ] Tests deep nested queries (post.comments.author)
- [ ] Validates response data shape
- [ ] Detects missing fields in responses
- [ ] Handles both GraphQL and REST endpoints
- [ ] Generates query support matrix

### Step 4: Create N+1 Query Detector

**File**: `tests/qa/n1_detector.py`

```python
"""
N+1 Query Detector - Detects N+1 query patterns

Tests:
1. Monitors database query count during GraphQL operations
2. Detects if fetching N items triggers N+1 database queries
3. Validates DataLoader/batching is working correctly

Approach:
- Enable PostgreSQL query logging
- Execute test queries that should trigger batching
- Count actual database queries executed
- Compare against expected query count

Outputs:
- Query count per operation
- N+1 detection results
- Batching efficiency score
"""

import asyncpg
from typing import Dict, List
import re

class N1Detector:
    """Detects N+1 query anti-patterns."""

    async def connect_to_db(self, db_url: str):
        """Connect directly to PostgreSQL for query monitoring."""
        pass

    async def enable_query_logging(self):
        """
        Enable PostgreSQL query logging for this session.

        Options:
        1. Use pg_stat_statements extension
        2. Set log_statement = 'all' for session
        3. Use EXPLAIN ANALYZE
        """
        # Reset statistics
        await self.conn.execute("SELECT pg_stat_statements_reset()")
        pass

    async def get_query_count(self) -> int:
        """
        Get number of queries executed since last reset.

        Query:
            SELECT COUNT(*) FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat%'
        """
        pass

    async def test_n1_pattern(
        self,
        framework: Dict,
        test_case: str
    ) -> Dict:
        """
        Test for N+1 queries.

        Test cases:
        1. "users_with_posts": Fetch 10 users with their posts
           - Expected queries: 1 (users) + 1 (batched posts) = 2
           - N+1 pattern: 1 (users) + 10 (individual post queries) = 11

        2. "posts_with_authors_and_comments": Fetch 10 posts with authors and comments
           - Expected: 1 (posts) + 1 (authors) + 1 (comments) = 3
           - N+1 pattern: 1 + 10 + 10 = 21

        Returns:
            {
                'test_case': 'users_with_posts',
                'items_fetched': 10,
                'query_count': 2,
                'expected_query_count': 2,
                'status': 'pass' | 'fail',
                'efficiency_score': 1.0,  # expected / actual
                'has_n1_pattern': False
            }
        """
        pass

    async def analyze_query_patterns(self, queries: List[str]) -> Dict:
        """
        Analyze query patterns to detect batching.

        Look for:
        - "WHERE id = ANY($1)" - batch loading pattern
        - "WHERE id IN (...)" - batch loading pattern
        - "WHERE id = $1" in loop - N+1 pattern
        """
        pass

# Test cases for N+1 detection:
N1_TEST_CASES = {
    'users_with_posts': {
        'query': '''
            query {
                users(limit: 10) {
                    id
                    username
                    posts(limit: 5) {
                        id
                        title
                    }
                }
            }
        ''',
        'expected_queries': 2,  # 1 for users, 1 batched for all posts
        'max_acceptable_queries': 3
    },
    'posts_with_authors': {
        'query': '''
            query {
                posts(limit: 10) {
                    id
                    title
                    author {
                        id
                        username
                    }
                }
            }
        ''',
        'expected_queries': 2,  # 1 for posts, 1 batched for authors
        'max_acceptable_queries': 3
    },
    'posts_with_comments_and_authors': {
        'query': '''
            query {
                posts(limit: 10) {
                    id
                    title
                    comments(limit: 5) {
                        id
                        content
                        author {
                            username
                        }
                    }
                }
            }
        ''',
        'expected_queries': 3,  # posts, comments (batched), authors (batched)
        'max_acceptable_queries': 4
    }
}
```

**Acceptance Criteria**:
- [ ] Connects to PostgreSQL and monitors queries
- [ ] Resets query statistics before each test
- [ ] Executes test queries against framework
- [ ] Counts actual database queries executed
- [ ] Detects N+1 patterns (query count > expected)
- [ ] Calculates efficiency score
- [ ] Generates N+1 detection report for each framework

### Step 5: Create Data Consistency Validator

**File**: `tests/qa/data_consistency_validator.py`

```python
"""
Data Consistency Validator - Verifies all frameworks return identical data

Tests:
1. Execute same query against all frameworks
2. Compare response data for consistency
3. Verify field names match (camelCase vs snake_case handling)
4. Verify data values are identical

Outputs:
- Data consistency matrix
- Frameworks that return different data
- Field name mapping issues
"""

import httpx
from typing import Dict, List, Any
from deepdiff import DeepDiff  # For deep comparison

class DataConsistencyValidator:
    """Validates data consistency across frameworks."""

    async def fetch_from_all_frameworks(
        self,
        query: str,
        variables: Dict = None
    ) -> Dict[str, Any]:
        """
        Execute same query against all running frameworks.

        Returns:
            {
                'fraiseql': {'data': {...}, 'errors': None},
                'strawberry': {'data': {...}, 'errors': None},
                ...
            }
        """
        pass

    def normalize_response(self, data: Any, framework: Dict) -> Any:
        """
        Normalize response for comparison.

        - Convert camelCase to snake_case or vice versa
        - Sort lists for consistent comparison
        - Handle null vs missing fields
        """
        pass

    async def compare_responses(
        self,
        responses: Dict[str, Any]
    ) -> Dict:
        """
        Compare responses from all frameworks.

        Returns:
            {
                'status': 'pass' | 'fail',
                'baseline': 'fraiseql',  # Framework used as baseline
                'differences': {
                    'strawberry': [],  # No differences
                    'graphene': [
                        {
                            'field': 'user.firstName',
                            'expected': 'John',
                            'actual': 'Jane',
                            'type': 'value_mismatch'
                        }
                    ],
                    'async-graphql': [
                        {
                            'field': 'user',
                            'expected': {...},
                            'actual': None,
                            'type': 'missing_data'
                        }
                    ]
                }
            }
        """
        pass

    async def verify_field_naming(self, responses: Dict[str, Any]) -> Dict:
        """
        Verify field naming conventions are correct.

        Check:
        - GraphQL should use camelCase (firstName, lastName)
        - Database uses snake_case (first_name, last_name)
        - Frameworks properly convert between conventions
        """
        pass

# Standard test data for consistency testing:
CONSISTENCY_TESTS = [
    {
        'name': 'user_by_id',
        'query': 'query($id: ID!) { user(id: $id) { id username firstName lastName bio } }',
        'variables': {'id': 'test-user-1'},
        'check_fields': ['id', 'username', 'firstName', 'lastName', 'bio']
    },
    {
        'name': 'users_list',
        'query': 'query { users(limit: 5) { id username } }',
        'check_ordering': True,  # Should return in consistent order
        'check_count': True  # Should return same number of results
    },
    # ... more tests
]
```

**Acceptance Criteria**:
- [ ] Executes same queries against all frameworks
- [ ] Normalizes responses for fair comparison
- [ ] Detects data value mismatches
- [ ] Detects field naming issues (camelCase vs snake_case)
- [ ] Detects missing data (frameworks returning null/empty)
- [ ] Uses baseline framework (FraiseQL or Strawberry) for comparison
- [ ] Generates data consistency report

### Step 6: Create Config Validator

**File**: `tests/qa/config_validator.py`

```python
"""
Config Validator - Verifies framework configurations

Tests:
1. Connection pool configurations are correct
2. Statement caching is enabled where expected
3. Metrics endpoints are accessible
4. Health checks are working
5. Environment variables are set correctly

Outputs:
- Configuration audit report
- Missing configurations
- Configuration recommendations
"""

import httpx
from typing import Dict

class ConfigValidator:
    """Validates framework configurations."""

    async def check_health_endpoint(self, framework: Dict) -> Dict:
        """
        Check framework health endpoint.

        Expected response:
            {
                'status': 'healthy',
                'framework': 'fraiseql',
                'version': '1.8.1'  # optional
            }
        """
        pass

    async def check_metrics_endpoint(self, framework: Dict) -> Dict:
        """
        Check Prometheus metrics endpoint.

        Verify:
        - Endpoint returns 200
        - Returns prometheus text format
        - Contains relevant metrics (http_requests_total, etc.)
        """
        pass

    async def verify_pool_config(self, framework: Dict) -> Dict:
        """
        Verify connection pool configuration.

        For Python frameworks using common/async_db.py:
        - Check min_size and max_size match registry
        - Verify statement_cache_size is set

        Returns:
            {
                'status': 'pass' | 'fail',
                'expected_min': 10,
                'actual_min': 10,
                'expected_max': 50,
                'actual_max': 50,
                'statement_caching': True,
                'issues': []
            }
        """
        pass

    async def verify_database_connection(self, framework: Dict) -> Dict:
        """
        Verify framework can connect to database.

        Tests:
        - Health check includes database status
        - Can execute simple query
        - Connection pool is initialized
        """
        pass

# Configuration checks:
CONFIG_CHECKS = {
    'health_endpoint': {
        'required': True,
        'expected_status': 200,
        'expected_fields': ['status', 'framework']
    },
    'metrics_endpoint': {
        'required': False,  # Only some frameworks have this
        'expected_status': 200,
        'expected_format': 'prometheus'
    },
    'database_connection': {
        'required': True,
        'test_query': 'SELECT 1'
    }
}
```

**Acceptance Criteria**:
- [ ] Checks health endpoints for all frameworks
- [ ] Checks metrics endpoints where available
- [ ] Verifies database connectivity
- [ ] Validates pool configuration matches registry
- [ ] Generates configuration audit report

### Step 7: Create Performance Validator

**File**: `tests/qa/performance_validator.py`

```python
"""
Performance Validator - Basic performance sanity checks

NOT comprehensive benchmarking - just sanity checks to detect broken implementations.

Tests:
1. Response times are within acceptable ranges
2. No frameworks are orders of magnitude slower than others
3. No frameworks timing out
4. No frameworks consuming excessive memory

Outputs:
- Performance sanity check results
- Frameworks that fail basic performance criteria
"""

import httpx
import asyncio
import psutil
from typing import Dict, List

class PerformanceValidator:
    """Basic performance sanity checks."""

    async def measure_query_latency(
        self,
        framework: Dict,
        query: str,
        iterations: int = 10
    ) -> Dict:
        """
        Measure query latency.

        Returns:
            {
                'framework': 'fraiseql',
                'query': 'ping',
                'iterations': 10,
                'avg_latency_ms': 5.2,
                'min_latency_ms': 3.1,
                'max_latency_ms': 12.5,
                'p95_latency_ms': 10.1,
                'p99_latency_ms': 11.8
            }
        """
        pass

    async def check_timeout_rate(
        self,
        framework: Dict,
        timeout_ms: int = 5000
    ) -> Dict:
        """
        Check if framework times out under normal load.

        Returns:
            {
                'framework': 'async-graphql',
                'total_requests': 100,
                'timeouts': 100,  # ❌ All requests timing out
                'timeout_rate': 1.0,
                'status': 'fail'
            }
        """
        pass

    async def compare_relative_performance(
        self,
        results: Dict[str, Dict]
    ) -> Dict:
        """
        Compare framework performance relatively.

        Detect outliers:
        - Framework >10x slower than median: ❌ Likely broken
        - Framework >3x slower than median: ⚠️ Investigate
        - Framework within 3x of median: ✅ OK for QA purposes

        Returns:
            {
                'baseline_median_ms': 5.0,
                'outliers': [
                    {
                        'framework': 'async-graphql',
                        'latency_ms': 5000,  # Timing out
                        'multiple_of_median': 1000,
                        'status': 'critical'
                    }
                ]
            }
        """
        pass

# Performance thresholds:
PERFORMANCE_THRESHOLDS = {
    'ping_query': {
        'max_latency_ms': 100,  # Ping should be <100ms
        'max_timeout_rate': 0.01  # <1% timeout rate
    },
    'simple_query': {
        'max_latency_ms': 500,  # Simple queries <500ms
        'max_timeout_rate': 0.05
    },
    'complex_query': {
        'max_latency_ms': 2000,  # Complex queries <2s
        'max_timeout_rate': 0.1
    }
}
```

**Acceptance Criteria**:
- [ ] Measures basic query latency (ping, user, users)
- [ ] Detects timeouts and high timeout rates
- [ ] Compares relative performance across frameworks
- [ ] Identifies critical outliers (>10x slower)
- [ ] Generates performance sanity check report
- [ ] Does NOT attempt comprehensive benchmarking (that's separate)

### Step 8: Create Main Validator Orchestrator

**File**: `tests/qa/framework_validator.py`

```python
"""
Main Framework Validator - Orchestrates all validation checks

Runs all validators in order and generates comprehensive report.
"""

import asyncio
from pathlib import Path
import yaml
import json
from datetime import datetime

from .schema_validator import SchemaValidator
from .query_validator import QueryValidator
from .n1_detector import N1Detector
from .data_consistency_validator import DataConsistencyValidator
from .config_validator import ConfigValidator
from .performance_validator import PerformanceValidator

class FrameworkValidator:
    """Main validation orchestrator."""

    def __init__(self, registry_path: str, config_path: str):
        """Load framework registry and validation config."""
        self.registry = self._load_yaml(registry_path)
        self.config = self._load_yaml(config_path)

        # Initialize validators
        self.schema_validator = SchemaValidator()
        self.query_validator = QueryValidator()
        self.n1_detector = N1Detector()
        self.consistency_validator = DataConsistencyValidator()
        self.config_validator = ConfigValidator()
        self.performance_validator = PerformanceValidator()

    async def validate_all_frameworks(self) -> Dict:
        """
        Run all validation checks against all frameworks.

        Returns comprehensive validation report.
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_frameworks': len(self.registry['frameworks']),
            'frameworks': {}
        }

        for framework in self.registry['frameworks']:
            print(f"\n{'='*60}")
            print(f"Validating: {framework['name']} ({framework['language']} - {framework['type']})")
            print(f"{'='*60}")

            framework_results = await self._validate_framework(framework)
            results['frameworks'][framework['name']] = framework_results

        # Generate summary
        results['summary'] = self._generate_summary(results)

        return results

    async def _validate_framework(self, framework: Dict) -> Dict:
        """Run all validation checks for a single framework."""
        results = {
            'framework': framework['name'],
            'language': framework['language'],
            'type': framework['type'],
            'checks': {}
        }

        # 1. Schema validation
        print(f"  [1/6] Validating schema references...")
        results['checks']['schema'] = await self.schema_validator.verify_framework_schema(framework)

        # 2. Config validation
        print(f"  [2/6] Validating configuration...")
        results['checks']['config'] = {
            'health': await self.config_validator.check_health_endpoint(framework),
            'metrics': await self.config_validator.check_metrics_endpoint(framework),
            'pool': await self.config_validator.verify_pool_config(framework),
            'database': await self.config_validator.verify_database_connection(framework)
        }

        # 3. Query validation
        print(f"  [3/6] Validating query support...")
        results['checks']['queries'] = await self.query_validator.verify_query_support(framework)

        # 4. N+1 detection
        print(f"  [4/6] Detecting N+1 query patterns...")
        results['checks']['n1_queries'] = {
            'users_with_posts': await self.n1_detector.test_n1_pattern(framework, 'users_with_posts'),
            'posts_with_authors': await self.n1_detector.test_n1_pattern(framework, 'posts_with_authors'),
            'posts_with_comments_and_authors': await self.n1_detector.test_n1_pattern(framework, 'posts_with_comments_and_authors')
        }

        # 5. Performance sanity checks
        print(f"  [5/6] Running performance sanity checks...")
        results['checks']['performance'] = {
            'ping': await self.performance_validator.measure_query_latency(framework, 'ping'),
            'simple_query': await self.performance_validator.measure_query_latency(framework, 'user'),
            'timeout_rate': await self.performance_validator.check_timeout_rate(framework)
        }

        # 6. Data consistency (compared to baseline)
        print(f"  [6/6] Checking data consistency...")
        # This will be run once across all frameworks after individual checks

        # Calculate overall status
        results['overall_status'] = self._calculate_status(results['checks'])

        return results

    def _calculate_status(self, checks: Dict) -> str:
        """
        Calculate overall status based on all checks.

        Returns: 'pass' | 'warning' | 'fail' | 'broken'
        """
        # Check for broken status
        if checks.get('config', {}).get('health', {}).get('status') == 'fail':
            return 'broken'  # Framework not running

        if checks.get('queries', {}).get('supported_queries', {}).get('ping') == 'fail':
            return 'broken'  # Most basic query fails

        # Check for critical failures
        critical_failures = [
            checks.get('schema', {}).get('status') == 'fail',
            len(checks.get('queries', {}).get('issues', [])) > 5,  # Many query failures
            checks.get('n1_queries', {}).get('users_with_posts', {}).get('has_n1_pattern') == True
        ]

        if any(critical_failures):
            return 'fail'

        # Check for warnings
        warnings = [
            len(checks.get('schema', {}).get('issues', [])) > 0,
            checks.get('performance', {}).get('timeout_rate', {}).get('timeout_rate', 0) > 0.01
        ]

        if any(warnings):
            return 'warning'

        return 'pass'

    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary statistics."""
        frameworks = results['frameworks']

        statuses = [f['overall_status'] for f in frameworks.values()]

        return {
            'total_frameworks': len(frameworks),
            'status_breakdown': {
                'pass': statuses.count('pass'),
                'warning': statuses.count('warning'),
                'fail': statuses.count('fail'),
                'broken': statuses.count('broken')
            },
            'broken_frameworks': [
                name for name, f in frameworks.items()
                if f['overall_status'] == 'broken'
            ],
            'failing_frameworks': [
                name for name, f in frameworks.items()
                if f['overall_status'] == 'fail'
            ]
        }

    async def generate_report(self, results: Dict, output_path: str):
        """Generate markdown validation report."""
        report = []

        report.append("# Framework Validation Report\n")
        report.append(f"**Generated**: {results['timestamp']}\n")
        report.append(f"**Total Frameworks**: {results['total_frameworks']}\n\n")

        # Summary
        report.append("## Summary\n")
        summary = results['summary']
        report.append(f"- ✅ **Pass**: {summary['status_breakdown']['pass']}")
        report.append(f"- ⚠️ **Warning**: {summary['status_breakdown']['warning']}")
        report.append(f"- ❌ **Fail**: {summary['status_breakdown']['fail']}")
        report.append(f"- 🚨 **Broken**: {summary['status_breakdown']['broken']}\n")

        if summary['broken_frameworks']:
            report.append("\n### 🚨 Broken Frameworks (Not Running)\n")
            for name in summary['broken_frameworks']:
                report.append(f"- {name}")

        if summary['failing_frameworks']:
            report.append("\n### ❌ Failing Frameworks\n")
            for name in summary['failing_frameworks']:
                report.append(f"- {name}")

        # Individual framework results
        report.append("\n## Individual Framework Results\n")

        for name, framework in results['frameworks'].items():
            status_icon = {
                'pass': '✅',
                'warning': '⚠️',
                'fail': '❌',
                'broken': '🚨'
            }[framework['overall_status']]

            report.append(f"\n### {status_icon} {name} ({framework['language']} - {framework['type']})\n")
            report.append(f"**Overall Status**: {framework['overall_status'].upper()}\n")

            # Schema check
            schema = framework['checks'].get('schema', {})
            report.append(f"\n**Schema Validation**: {schema.get('status', 'unknown')}")
            if schema.get('missing_tables'):
                report.append(f"  - Missing tables: {', '.join(schema['missing_tables'])}")
            if schema.get('issues'):
                report.append(f"  - Issues: {len(schema['issues'])}")

            # Query support
            queries = framework['checks'].get('queries', {})
            supported = queries.get('supported_queries', {})
            passing = sum(1 for v in supported.values() if v == 'pass')
            total = len(supported)
            report.append(f"\n**Query Support**: {passing}/{total} queries passing")

            failing_queries = [q for q, s in supported.items() if s == 'fail']
            if failing_queries:
                report.append(f"  - Failing: {', '.join(failing_queries)}")

            # N+1 detection
            n1 = framework['checks'].get('n1_queries', {})
            has_n1 = any(test.get('has_n1_pattern') for test in n1.values())
            report.append(f"\n**N+1 Queries**: {'❌ Detected' if has_n1 else '✅ None detected'}")

            # Performance
            perf = framework['checks'].get('performance', {})
            ping_latency = perf.get('ping', {}).get('avg_latency_ms', 0)
            timeout_rate = perf.get('timeout_rate', {}).get('timeout_rate', 0)
            report.append(f"\n**Performance**: Ping {ping_latency:.1f}ms avg, {timeout_rate*100:.1f}% timeout rate")

        # Write report
        with open(output_path, 'w') as f:
            f.write('\n'.join(report))

        print(f"\n✅ Report generated: {output_path}")

    async def generate_json_report(self, results: Dict, output_path: str):
        """Generate JSON validation report for programmatic use."""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"✅ JSON report generated: {output_path}")


# CLI entry point
async def main():
    """Main entry point for validation."""
    validator = FrameworkValidator(
        registry_path='tests/qa/framework_registry.yaml',
        config_path='tests/qa/validation_config.yaml'
    )

    print("Starting comprehensive framework validation...\n")
    results = await validator.validate_all_frameworks()

    # Generate reports
    await validator.generate_report(
        results,
        '.phases/qa-framework-verification/VERIFICATION_RESULTS.md'
    )
    await validator.generate_json_report(
        results,
        '.phases/qa-framework-verification/verification_results.json'
    )

    # Exit code based on results
    if results['summary']['status_breakdown']['broken'] > 0:
        print("\n🚨 CRITICAL: Some frameworks are broken and not running!")
        return 2
    elif results['summary']['status_breakdown']['fail'] > 0:
        print("\n❌ FAIL: Some frameworks failed validation!")
        return 1
    elif results['summary']['status_breakdown']['warning'] > 0:
        print("\n⚠️ WARNING: Some frameworks have issues but are functional")
        return 0
    else:
        print("\n✅ SUCCESS: All frameworks passed validation!")
        return 0


if __name__ == '__main__':
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

**Acceptance Criteria**:
- [ ] Runs all validators in sequence
- [ ] Generates comprehensive validation report
- [ ] Generates JSON report for programmatic access
- [ ] Calculates overall status for each framework
- [ ] Provides summary statistics
- [ ] Returns appropriate exit codes (0=pass, 1=fail, 2=broken)

### Step 9: Create Test Fixtures

**File**: `tests/qa/fixtures/test_queries.json`

```json
{
  "graphql_queries": {
    "ping": {
      "query": "query { ping }",
      "variables": {},
      "expected_response": {
        "data": {
          "ping": "pong"
        }
      }
    },
    "user": {
      "query": "query($id: ID!) { user(id: $id) { id username firstName lastName bio } }",
      "variables": {
        "id": "{{TEST_USER_ID}}"
      },
      "expected_fields": ["id", "username", "firstName", "lastName", "bio"]
    },
    "users": {
      "query": "query($limit: Int!) { users(limit: $limit) { id username } }",
      "variables": {
        "limit": 5
      },
      "expected_min_count": 1,
      "expected_fields": ["id", "username"]
    },
    "user_with_posts": {
      "query": "query($id: ID!) { user(id: $id) { id username posts(limit: 5) { id title content } } }",
      "variables": {
        "id": "{{TEST_USER_ID}}"
      },
      "expected_relationships": ["posts"],
      "n1_test": true,
      "expected_query_count": 2
    },
    "posts_with_author_and_comments": {
      "query": "query($limit: Int!) { posts(limit: $limit) { id title author { id username } comments(limit: 5) { id content author { username } } } }",
      "variables": {
        "limit": 10
      },
      "expected_relationships": ["author", "comments", "comments.author"],
      "n1_test": true,
      "expected_query_count": 3
    }
  },
  "rest_queries": {
    "ping": {
      "method": "GET",
      "path": "/ping",
      "expected_response": {
        "message": "pong"
      }
    },
    "user": {
      "method": "GET",
      "path": "/users/{{TEST_USER_ID}}",
      "expected_fields": ["id", "username", "firstName", "lastName", "bio"]
    },
    "user_with_posts": {
      "method": "GET",
      "path": "/users/{{TEST_USER_ID}}?include=posts",
      "expected_fields": ["id", "username", "posts"],
      "n1_test": true
    }
  },
  "mutations": {
    "update_user": {
      "query": "mutation($id: ID!, $bio: String) { updateUser(id: $id, bio: $bio) { id bio } }",
      "variables": {
        "id": "{{TEST_USER_ID}}",
        "bio": "Updated bio for testing"
      },
      "cleanup_query": "mutation($id: ID!, $bio: String) { updateUser(id: $id, bio: $bio) { id bio } }",
      "cleanup_variables": {
        "id": "{{TEST_USER_ID}}",
        "bio": "Original bio"
      }
    }
  }
}
```

### Step 10: Create Validation Config

**File**: `tests/qa/validation_config.yaml`

```yaml
# Validation configuration and thresholds

database:
  url: postgresql://benchmark:benchmark123@postgres:5432/fraiseql_benchmark
  test_user_id: "{{WILL_BE_FETCHED}}"  # Fetch first user from database
  test_post_id: "{{WILL_BE_FETCHED}}"
  test_comment_id: "{{WILL_BE_FETCHED}}"

thresholds:
  performance:
    ping_query_max_ms: 100
    simple_query_max_ms: 500
    complex_query_max_ms: 2000
    max_timeout_rate: 0.01  # 1%

  n1_queries:
    max_query_multiplier: 1.5  # Actual queries should be ≤ 1.5x expected

  data_consistency:
    allow_field_name_variations: true  # Allow camelCase vs snake_case
    require_identical_values: true

validation_steps:
  - name: schema_validation
    enabled: true
    critical: true

  - name: config_validation
    enabled: true
    critical: true

  - name: query_validation
    enabled: true
    critical: true

  - name: n1_detection
    enabled: true
    critical: false  # Warning only, not blocking

  - name: data_consistency
    enabled: true
    critical: false  # Warning only

  - name: performance_sanity
    enabled: true
    critical: false  # Warning only

reporting:
  output_formats:
    - markdown
    - json
  output_directory: .phases/qa-framework-verification

  include_sections:
    - summary
    - individual_results
    - recommendations
    - schema_documentation

baseline_framework: fraiseql  # Use as baseline for data consistency
```

## Verification Commands

After implementation, verify the QA system works:

```bash
# 1. Install dependencies
cd tests/qa
pip install -r requirements.txt

# 2. Ensure database is running
docker-compose up -d postgres

# 3. Ensure all frameworks are running
./scripts/start-all-frameworks.sh

# 4. Run schema validator only
python -m tests.qa.schema_validator

# 5. Run query validator only
python -m tests.qa.query_validator

# 6. Run N+1 detector only
python -m tests.qa.n1_detector

# 7. Run full validation suite
python -m tests.qa.framework_validator

# 8. View results
cat .phases/qa-framework-verification/VERIFICATION_RESULTS.md
```

**Expected Output**:
```
Starting comprehensive framework validation...

============================================================
Validating: fraiseql (python - graphql)
============================================================
  [1/6] Validating schema references... ✅ PASS
  [2/6] Validating configuration... ✅ PASS
  [3/6] Validating query support... ✅ PASS (10/10 queries)
  [4/6] Detecting N+1 query patterns... ✅ PASS (no N+1 detected)
  [5/6] Running performance sanity checks... ✅ PASS (5ms avg)
  [6/6] Checking data consistency... ⏭️  SKIPPED (baseline)

Overall Status: ✅ PASS

============================================================
Validating: async-graphql (rust - graphql)
============================================================
  [1/6] Validating schema references... ✅ PASS
  [2/6] Validating configuration... ✅ PASS
  [3/6] Validating query support... ❌ FAIL (0/10 queries)
  [4/6] Detecting N+1 query patterns... ⏭️  SKIPPED (queries failed)
  [5/6] Running performance sanity checks... ❌ FAIL (100% timeout rate)
  [6/6] Checking data consistency... ❌ FAIL (all data missing)

Overall Status: 🚨 BROKEN

... (continue for all 23 frameworks)

============================================================
Summary
============================================================
Total Frameworks: 23
✅ Pass: 18
⚠️ Warning: 3
❌ Fail: 1
🚨 Broken: 1

🚨 Broken Frameworks:
  - async-graphql (Rust GraphQL) - No queries implemented

❌ Failing Frameworks:
  - fastapi-rest (Python REST) - Wrong table names

✅ Report generated: .phases/qa-framework-verification/VERIFICATION_RESULTS.md
✅ JSON report generated: .phases/qa-framework-verification/verification_results.json
```

## Acceptance Criteria

### Phase Completion Criteria

- [ ] All 7 validator modules implemented and tested
- [ ] Framework registry contains all 23 frameworks
- [ ] Test fixtures created with standard queries
- [ ] Validation config file created
- [ ] Main orchestrator runs all validators
- [ ] Markdown report generated successfully
- [ ] JSON report generated successfully
- [ ] Documentation (README.md) created

### Validation Success Criteria

- [ ] Schema validator detects table name mismatches
- [ ] Query validator detects broken implementations (async-graphql)
- [ ] N+1 detector identifies frameworks without batching
- [ ] Data consistency validator compares framework responses
- [ ] Config validator checks health/metrics endpoints
- [ ] Performance validator detects timeout/broken frameworks
- [ ] Exit codes correctly indicate pass/warning/fail/broken status

### Report Quality Criteria

- [ ] Summary shows breakdown of framework statuses
- [ ] Individual framework results are detailed
- [ ] Broken frameworks are clearly highlighted
- [ ] Recommendations are actionable
- [ ] JSON report is valid and parseable

## DO NOT

- ❌ Do NOT run actual benchmarks - this is QA only, not performance testing
- ❌ Do NOT modify framework implementations - only validate them
- ❌ Do NOT make assumptions about table names - detect actual schema
- ❌ Do NOT skip validation steps silently - report all results
- ❌ Do NOT use placeholder data - fetch real test IDs from database
- ❌ Do NOT hardcode framework URLs - use registry configuration
- ❌ Do NOT fail on warnings - distinguish between fail and warning
- ❌ Do NOT ignore broken frameworks - report them prominently

## Success Metrics

After this phase completes successfully:

1. **Visibility**: Clear understanding of which frameworks are functional
2. **Confidence**: Know which frameworks can be benchmarked fairly
3. **Documentation**: Comprehensive validation report
4. **Automation**: Repeatable validation process for future changes
5. **Prioritization**: Know which frameworks need fixes before benchmarking

The validation report will be the foundation for deciding:
- Which frameworks to include in benchmarks
- Which implementations need fixes
- Whether benchmarking can proceed or requires fixes first
