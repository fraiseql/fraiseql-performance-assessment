# FraiseQL Framework - Complete Capabilities Map

**Version**: 1.8.2 (Stable)
**Python**: 3.13+
**PostgreSQL**: 13+
**Status**: Production-ready

---

## Executive Summary

FraiseQL is a **comprehensive enterprise GraphQL framework** combining Python's developer experience with Rust's performance. It's not just a query builder—it's a complete GraphQL platform with 15 major capability categories spanning security, performance, automation, and enterprise features.

**Key differentiator**: Rust-first execution pipeline with zero Python serialization overhead, plus comprehensive auto-generation of mutations, queries, filters, and ordering.

---

## 1. CORE GRAPHQL OPERATIONS

### Queries
- Decorator-based query registration (`@query`)
- Type hint → GraphQL argument conversion
- Custom resolver logic support
- Error handling and exception translation

### Mutations
- PostgreSQL function-based mutations with introspection
- Union response types (Success | Error | custom types)
- Three error handling modes:
  - **DEFAULT**: Errors in payload with status
  - **ALWAYS_DATA**: Always return data field even on error
  - **STRICT_STATUS**: Status codes only, no error details
- Fragment support (inline & named)
- Field selection set analysis for efficient responses
- Error metadata with structured status codes

**Example**:
```python
@mutation
async def create_user(info, name: str, email: str) -> UserResult:
    # Mutation response: Success { id, name, email } | Error { message }
    pass
```

### Subscriptions (WebSocket)
- Full GraphQL-WS protocol support
- Connection state management
- Message filtering and caching
- Complexity analysis for subscriptions
- Lifecycle hooks (`with_lifecycle`)
- Production-ready WebSocket handling

### Directives & Schema Control
- Field-level directive support
- Custom directive definitions
- Schema validation before execution

---

## 2. DATABASE INTEGRATION

### PostgreSQL Native Support
- **Direct PostgreSQL optimizations** - Not a generic database ORM
- **Connection pooling** - asyncpg `AsyncConnectionPool` with health checks
- **Type adapters** - Preserve dates as strings, handle JSONB natively
- **Graceful connection handling** - Automatic retry on terminated connections

### JSONB Support
- **Nested JSONB querying** - Filter on JSONB paths and contents
- **Operators**: `contains`, `path`, hierarchical filtering
- **JSONB merging** - Incremental updates via `jsonb_merge_shallow()`
- **Automatic parsing** - JSONB fields converted to types

### Array Support
- **Array operators**: `@>` (contains), `<@` (contained_by), `&&` (overlaps)
- **Array length**: `len_eq`, `len_gt`, `len_lt`, `len_gte`
- **Array element tests**: `any_eq`, `all_eq` (SQL ANY/ALL)
- **Nested array filtering** - WHERE clauses on array elements
- **Auto-discovery**: `@auto_nested_array_filters` decorator

**Example**:
```python
# WHERE tags @> '["python"]'
users(where: {tags: {contains: ["python"]}})
```

### Vector/Embedding Support (pgvector)
- **6 distance operators**:
  - Cosine similarity: `<=>`
  - L2 distance: `<->`
  - L1 distance: `<+>`
  - Hamming distance: `<~>`
  - Jaccard distance: `<%>`
  - Dot product: `<#>`
- **Vector types**: Native pgvector integration
- **Use case**: ML embeddings, semantic search, RAG

**Example**:
```python
# WHERE embedding <=> query_vector < 0.5
similar_items(where: {
    embedding: {cosine_distance_lt: {value: query_vec, distance: 0.5}}
})
```

### Full-Text Search (PostgreSQL FTS)
- **Query types**:
  - `plainto_tsquery()` - Plain text search
  - Phrase queries with quotes
  - WebSearch queries (Google-like syntax)
- **Search operators**: `@@` tsvector matching
- **Ranking**: `rank_gt`, `rank_lt`, `rank_cd_gt`, `rank_cd_lt`
- **Text vectors**: Automatic tsvector generation and indexing

**Example**:
```python
# WHERE search_vector @@ plainto_tsquery('database')
posts(where: {search: {query: "database OR performance"}})
```

### Network/INET/CIDR Support
- **CIDR operators**:
  - `inSubnet` (`<<=`) - Contained by subnet
  - `overlaps` (`&&`) - CIDR overlap
  - Strict comparison: `<<` (strictly left), `>>` (strictly right)
- **IPv4/IPv6 detection**: `isIPv4`, `isIPv6`
- **Private range detection**: Smart CIDR validation
- **Network operations**: Full network arithmetic

**Example**:
```python
# WHERE ip_address <<= '192.168.0.0/16'::cidr
internal_ips(where: {
    ipAddress: {inSubnet: "192.168.0.0/16"}
})
```

### MAC Address Support
- Type-specific filtering for IEEE 802 MAC addresses
- Format validation

### Date Range Support
- **DateRange operators**:
  - `contains_date` - Date within range
  - `adjacent` (`-|-`) - Adjacent date ranges
  - `overlap` - Overlapping ranges
- **Range boundaries** - Inclusive/exclusive range queries
- **Range arithmetic** - Full PostgreSQL range operations

---

## 3. SECURITY FEATURES (Enterprise-Grade)

### Authentication
- **Auth0 integration** - Full Auth0 provider with token revocation
- **Native authentication** - Built-in token generation/management
- **Token revocation** - Immediate invalidation
- **Middleware injection** - Automatic user context population
- **Decorators**: `@requires_auth`, `@requires_role`, `@requires_permission`

### RBAC (Role-Based Access Control)
- **Hierarchical roles** - Multi-level role inheritance (org → team → user)
- **Permission system** - Granular, nested permissions
- **Multi-tenant support** - Tenant-aware permission caching
- **PostgreSQL UNLOGGED table caching** - 0.1-0.3ms lookup time
- **Domain versioning** - Automatic cache invalidation on role/permission changes
- **CASCADE rules** - Hierarchical cache invalidation
- **Scale**: Designed for 10,000+ users per tenant

**Example**:
```python
@requires_role("admin")
@requires_permission("posts:delete")
@mutation
async def delete_post(info, id: int) -> DeletePostResult:
    pass
```

### Field-Level Authorization
- **Per-field access control** - Restrict field access by role/permission
- **Real-time enforcement** - Validation during resolver execution
- **Automatic integration** - Works transparently with resolvers

### Rate Limiting
- **Request rate limiting** - Prevent API abuse and DoS
- **Query complexity limits** - Restrict expensive queries
- **Per-user limits** - Different limits per authenticated user
- **Sliding window limiting** - Time-based throttling

### CSRF Protection
- **CSRF token handling** - Automatic token generation/validation
- **Security headers** - X-CSRF-Token support
- **Double-submit cookies** - Optional CSRF pattern

### Security Headers
- **Automatic injection** - CORS, CSP, X-Frame-Options, etc.
- **Clickjacking protection** - X-Frame-Options configuration
- **Content-Security-Policy** - CSP generation
- **CORS configuration** - Flexible policy management

### Audit Logging (Comprehensive)
- **Event audit trail** - All mutations logged with timestamps
- **User tracking** - Who did what and when
- **Before/after snapshots** - Full change history
- **Compliance ready** - GDPR, HIPAA, SOX compliance
- **Event types**: CREATE, UPDATE, DELETE with full context
- **Query logging** - Track queries, mutations, subscriptions
- **Database integration** - Native PostgreSQL triggers

**Example**:
```
INSERT event: {
  user_id: "user_123",
  action: "CREATE",
  table: "users",
  before: null,
  after: {id: 1, name: "John"},
  timestamp: "2025-12-16T14:00:00Z"
}
```

### Encryption & Hashing
- **Password hashing**: Argon2 and bcrypt support
- **Secret signing**: HMAC-SHA256 signing
- **Key management**: AWS KMS, GCP KMS, Azure Key Vault integration

### Startup Security Checks
- **Pre-flight validation** - Security configuration checks
- **Vulnerability scanning** - SBOM checking
- **Default safety** - Secure configurations enforced

---

## 4. PERFORMANCE FEATURES

### Rust Execution Pipeline
- **Zero Python overhead** - Rust-native JSON response generation
- **JSONB → HTTP directly** - PostgreSQL → Rust → Response
- **Lazy loading** - Optional Rust optimization (ENV: `FRAISEQL_DISABLE_RUST=1`)
- **Null response caching** - 12x faster for empty results (no JSON parsing)
- **RustResponseBytes** - Efficient memory usage for large responses
- **Performance impact**: 3-5x faster than pure Python frameworks

### PostgreSQL-Native Caching
- **UNLOGGED table caching** - Ultra-fast cache storage (0.1-0.3ms)
- **Domain versioning** - Automatic cache invalidation on schema changes
- **RBAC cache** - Permission cache with version tracking
- **Result caching** - Query result caching with TTL
- **APQ caching** - Automatic persisted query caching
- **Schema analyzer caching** - Introspection result caching
- **TTL support** - Configurable cache expiration

### DataLoader Optimization
- **Batch loading** - Eliminate N+1 query problems
- **Decorator-based**: `@dataloader_field` for automatic batching
- **Custom loaders** - GenericForeignKeyLoader, ProjectLoader, UserLoader, etc.
- **Loader registry** - Central loader management
- **Performance gain**: Reduce 100+ queries to 5-10

### N+1 Query Detection
- **Automatic detection** - Track resolver execution patterns
- **Error alerts** - Warn on N+1 patterns in development
- **Performance metrics** - Monitor query efficiency
- **Development mode** - Optional detection context

### Query Complexity Analysis
- **Complexity scoring** - Calculate query cost before execution
- **Per-field costs** - Customizable field complexity values
- **Enforcement** - Prevent overly expensive queries
- **Monitoring** - Track slow query patterns

---

## 5. AUTO-GENERATION CAPABILITIES

### WhereType Auto-Generation
- **Automatic filter types** - Create WHERE input types from data types
- **Operator support** - Different operators for each field type:
  - String: `eq`, `contains`, `startsWith`, `endsWith`, `regex`, `search`
  - Number: `eq`, `gt`, `gte`, `lt`, `lte`
  - Date: `eq`, `before`, `after`, `between`
  - Array: `contains`, `overlaps`, `length`
  - Network: `inSubnet`, `overlaps`
  - Vector: All 6 distance operators
- **Nested filtering** - WHERE inputs for related entities
- **Safe type creation** - `safe_create_where_type()` with error handling

**Example**:
```graphql
input UserWhereInput {
  username: StringWhereInput
  email: EmailWhereInput
  createdAt: DateWhereInput
  tags: StringArrayWhereInput
  embedding: VectorWhereInput
}

input StringWhereInput {
  equals: String
  contains: String
  startsWith: String
  search: String  # Full-text search
  regex: String
}
```

### OrderBy Auto-Generation
- **Automatic sort types** - Create ORDER BY inputs from data types
- **Multi-field sorting** - Array of sort specifications
- **Direction support** - ASC/DESC enums
- **Null handling** - NULLS FIRST/LAST options

**Example**:
```graphql
input UserOrderByInput {
  username: SortDirection
  createdAt: SortDirection
  relevance: SortDirection
}

enum SortDirection {
  ASC
  DESC
}
```

### Mutation Auto-Generation
- **SQL function introspection** - Auto-discover mutation functions
- **Input type generation** - Convert function parameters to input types
- **Output type generation** - Convert return types to output types
- **Error handling** - Automatic error type generation
- **Schema registration** - Automatic schema integration

**Example**:
```python
# Auto-generated from SQL function:
# CREATE FUNCTION create_user(name text, email email) RETURNS user_result

@mutation
async def create_user(info, name: str, email: str) -> UserResult:
    pass
# Automatically becomes:
# mutation CreateUser($input: CreateUserInput!): CreateUserResult!
```

### Query Auto-Generation
- **View introspection** - Discover queryable views
- **Type inference** - Map PostgreSQL types to GraphQL types
- **Resolver generation** - Auto-create query resolvers
- **Pagination support** - Automatic pagination fields

### Type Generation (57+ Scalar Types)
Built-in scalar types including:

**Identifiers** (11): UUID, IBAN, ISIN, CUSIP, SEDOL, LEI, MIC, VIN, AirportCode, PortCode, LanguageCode

**Dates/Times** (6): Date, DateTime, Time, DateRange, Duration, Timezone

**Network** (6): IpAddress, CIDR, MacAddress, Hostname, DomainName, Port

**Locations** (3): Latitude, Longitude, Coordinate

**Finance** (5): Money, ExchangeRate, CurrencyCode, StockSymbol, ExchangeCode

**Web** (5): Email, URL, DomainName, Slug, MimeType

**Other** (15): Phone, Color, Markdown, HTML, Image, File, LocaleCode, And more...

### Input Type Auto-Generation
- **Automatic creation** - From output types
- **Filter inputs** - WHERE and ORDER BY types
- **Mutation inputs** - From function parameters
- **Validation rules** - Automatic input validation

---

## 6. ENTERPRISE FEATURES

### Multi-Tenancy
- **Automatic tenant isolation** - Tenant-aware filtering
- **Tenant-scoped RBAC** - Roles/permissions per tenant
- **Tenant-scoped caching** - Cache isolated per tenant
- **Per-tenant pools** - Connection pools per tenant
- **Data isolation** - Complete data separation

### CQRS Pattern (Command-Query Responsibility Segregation)
- **Command-Query separation** - Separate read and write paths
- **SQL functions for writes** - Transactional write operations
- **Materialized views for reads** - Optimized read queries
- **Repository pattern** - Consistent data access
- **Event sourcing ready** - Foundation for event sourcing

### Incremental View Maintenance (IVM)
- **Automatic IVM detection** - Find materialized view candidates
- **JSONB IVM support** - Efficient updates via `jsonb_merge_shallow()`
- **Trigger generation** - Auto-create update triggers
- **Performance recommendations** - Suggest optimization strategies
- **Benefit**: Avoid expensive view refreshes

**Example**:
```python
# Auto-IVM setup for materialized views
setup_auto_ivm(
    view_name="v_user_stats",
    source_table="users"
)
# Creates triggers to incrementally update instead of full refresh
```

### Database Migrations
- **Alembic integration** - Standard SQLAlchemy migrations
- **Auto-migration** - Automatic schema updates
- **Migration discovery** - Find and apply pending migrations
- **Version tracking** - Schema versioning

### Audit Logging
- **Comprehensive event logging** - All mutations tracked
- **Temporal queries** - Query historical state
- **Change snapshots** - Before/after values
- **User attribution** - Who made each change
- **Compliance reports** - GDPR/HIPAA ready

### Software Bill of Materials (SBOM)
- **Dependency tracking** - All dependencies enumerated
- **License compliance** - License compatibility checking
- **Vulnerability scanning** - Known CVE checking
- **CycloneDX format** - Industry-standard SBOM format

---

## 7. INTEGRATION FEATURES

### FastAPI Integration
- **Complete app factory** - `create_fraiseql_app()` function
- **Auto-routing** - Automatic GraphQL endpoint setup
- **Middleware stack** - CORS, rate limiting, CSRF
- **Context injection** - Database, user context, custom dependencies
- **Health checks** - Built-in health endpoints
- **Metrics export** - APQ metrics, performance tracking

**Example**:
```python
app = create_fraiseql_app(
    database_url="postgresql://localhost/db",
    types=[User, Post],
    queries=[users, user_by_id],
    mutations=[create_user],
    config=FraiseQLConfig(
        database_pool_size=20,
        introspection_policy=IntrospectionPolicy.PUBLIC,
        cors_enabled=True
    )
)
```

### APQ (Automatic Persisted Queries)
- **Query persistence** - Store and reuse queries
- **APQ caching** - Cache persisted queries
- **Compression** - Reduce query size via hashing
- **Query metrics** - Track APQ usage statistics
- **Modes**: OPTIONAL, REQUIRED, DISABLED

### Middleware System
- **APQ middleware** - Query persistence
- **Rate limiting** - Request throttling
- **Body size limiting** - Prevent large uploads
- **Custom middleware** - Extensible system

### Schema Auto-Discovery
- **PostgreSQL introspection** - Auto-discover schema
- **Convention patterns**:
  - Views: `v_*` (e.g., `v_user`)
  - Functions: `fn_*` (e.g., `fn_create_user`)
- **Custom patterns** - Override naming conventions
- **Schema filtering** - Include/exclude specific schemas
- **Full introspection** - Complete database mapping

### AI/ML Integrations
- **LangChain compatibility** - Use FraiseQL with LangChain
  - Tool integration - Create LangChain tools from queries
  - Agent support - Use GraphQL in agent workflows
- **LlamaIndex compatibility** - Use with LlamaIndex
  - Data loader integration
  - RAG support

### Distributed Tracing
- **OpenTelemetry support** - Full distributed tracing
- **GraphQL-specific tracing** - Query execution spans
- **Performance metrics** - Latency, throughput, error rates
- **Custom spans** - Instrument custom resolvers
- **Integration**: Jaeger, Datadog, NewRelic compatible

---

## 8. DATA TRANSFORMATION

### Type System (57+ Scalars)
Comprehensive scalar type library covering:
- Identifiers (UUID, IBAN, ISIN, CUSIP, SEDOL, LEI, MIC, VIN, etc.)
- Dates/Times (Date, DateTime, Time, DateRange, Duration, Timezone)
- Network (IpAddress, CIDR, MacAddress, Hostname, DomainName, Port)
- Locations (Latitude, Longitude, Coordinate)
- Finance (Money, ExchangeRate, CurrencyCode, StockSymbol)
- Web (Email, URL, DomainName, Slug, MimeType)
- Other (Phone, Color, Markdown, HTML, Image, File)

### Type Decorators
- `@type` / `@fraise_type` - GraphQL output type
- `@input` / `@fraise_input` - GraphQL input type
- `@enum` / `@fraise_enum` - GraphQL enum
- `@interface` / `@fraise_interface` - GraphQL interface

### Field Definitions
- `fraise_field()` - Rich field metadata
- **Default values** - Defaults and default_factory
- **Field purpose** - "input", "output", or "both"
- **Descriptions** - Auto-generated documentation
- **Custom naming** - Override GraphQL field name
- **Nested filtering** - Enable WHERE on array fields

**Example**:
```python
@type
class User:
    id: UUID
    name: str = fraise_field(description="User's full name")
    email: Email
    tags: list[str] = fraise_field(
        description="User tags",
        metadata={"nested_filter": True}  # Enable WHERE filtering
    )
```

### Pagination Support
- **Relay cursor pagination** - Standard GraphQL Relay pattern
- **Edge and PageInfo** - Cursor, hasNextPage, endCursor
- **Cursor-based pagination** - Efficient at any offset
- **Limit/offset support** - Traditional pagination
- **Cursor encoding** - Opaque cursor format

### Partial Instantiation
- **Sparse result handling** - Only instantiate requested fields
- **Nested objects** - Partial nested type instantiation
- **Performance** - Reduce memory for large results
- **Flexibility** - Handle missing optional fields

### Date Range Validation
- **Range validation** - Ensure valid date ranges
- **Mixin support** - Add validation to types
- **Custom validators** - Domain-specific rules
- **Error messages** - Detailed validation feedback

---

## 9. DEVELOPMENT & DEBUGGING

### CLI Tools
- `fraiseql generate` - Generate schema from database
- `fraiseql migrate` - Run database migrations
- `fraiseql init` - Initialize new project
- `fraiseql check` - Validate schema and configuration
- `fraiseql dev` - Development mode with hot reload
- `fraiseql doctor` - Diagnose project health
- `fraiseql sbom` - Generate software bill of materials
- `fraiseql turbo` - Manage Turbo optimization
- `fraiseql sql` - Execute raw SQL queries

### Debug Mode
- **Query debugging** - Inspect query execution
- **Resolver tracing** - See resolver call chain
- **SQL inspection** - View generated SQL
- **Performance profiling** - Identify slow operations

### Schema Validation
- **Pre-execution validation** - Catch errors early
- **Type checking** - Query validation against schema
- **Resolver validation** - Check resolver availability
- **Custom validators** - Domain-specific validation

### Introspection & Metadata
- **Schema introspection** - Inspect GraphQL schema
- **Type information** - Get type details
- **Field metadata** - Field information
- **Directive support** - Introspect directives
- **Introspection policies**:
  - DISABLED - No introspection
  - PUBLIC - Everyone (default)
  - AUTHENTICATED - Authenticated users only

### Comprehensive Error Handling
- **FraiseQLException** - Base exception
- **QueryValidationError** - Invalid query
- **WhereClauseError** - Invalid WHERE clause
- **DatabaseQueryError** - Database errors
- **PartialInstantiationError** - Object instantiation
- **TypeRegistrationError** - Type registration
- **ResolverError** - Resolver execution
- **User-friendly errors** - Customer-facing messages
- **Rich context** - Detailed error information

---

## 10. ADVANCED QUERY FEATURES

### WHERE Clause System
- **Normalized representation** - Canonical internal format
- **Dict-based syntax** - Python dict WHERE clauses
- **WhereInput types** - GraphQL input syntax
- **Unlimited nesting** - Complex AND/OR/NOT expressions
- **Type-specific operators** - Different operators per type
- **Null handling** - `isnull` operator
- **Custom scalars** - Support for all 57+ types

### Comparison Operators
- **Standard**: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`
- **Containment**: `in`, `nin`
- **String patterns**: `contains`, `icontains`, `startswith`, `istartswith`, `endswith`, `iendswith`, `like`, `ilike`
- **NULL checks**: `isnull`
- **Regex**: `regex`, `iregex`

### Operator Strategies
- **Base operators** - Standard comparison/containment
- **Advanced operators** - PostgreSQL-specific (network, vector, JSONB)
- **Fallback operators** - Generic implementations
- **Custom operators** - Register custom strategies
- **Strategy registry** - Central operator management

### SQL Generation
- **Safe SQL** - Prevent injection attacks
- **Type-aware** - Correct SQL for type
- **Nested subqueries** - WHERE on related entities
- **Complex expressions** - Boolean algebra
- **Parameter binding** - Parameterized queries via psycopg

### Query Normalization
- **Input normalization** - Standardize WHERE input
- **Type coercion** - Convert values to target types
- **Validation** - Ensure valid WHERE expressions

---

## 11. SCHEMA BUILDING & COMPOSITION

### Dynamic Schema Building
- **Runtime schema construction** - Build at startup
- **Modular composition** - Compose schemas from parts
- **Auto-discovery** - Discover types and resolvers
- **Registry-based** - Central type registry

### Schema Builders
- **QueryTypeBuilder** - Build Query type
- **MutationTypeBuilder** - Build Mutation type
- **SubscriptionTypeBuilder** - Build Subscription type
- **Schema composer** - Compose multiple schemas
- **Type constructor** - Create types from components

### Type Construction
- **Scalar resolution** - Map custom scalars
- **Composite types** - Build nested objects
- **Enum construction** - Create enum types
- **Union types** - Create union types

### Mutation Schema Generation
- **Union type generation** - Success/Error unions
- **Schema validation** - Ensure valid mutation schema
- **Result type customization** - Configure response shape

---

## 12. COMPATIBILITY

### Strawberry GraphQL Compatibility
- **Drop-in replacement** - Use FraiseQL like Strawberry
- **API compatibility** - StrawberryCompatibility class
- **Aliased decorators** - All standard decorators supported
- **Migration path** - Easy migration from Strawberry

---

## 13. CONFIGURATION

### FastAPI Configuration (FraiseQLConfig)
- **Database URL** - PostgreSQL connection string
- **Introspection policy** - Control schema introspection
- **APQ mode** - Persisted query configuration
- **CORS settings** - Cross-origin configuration
- **Rate limiting** - Throttling configuration
- **Error config** - Mutation error behavior modes
- **Pool settings** - Connection pool configuration
- **Query depth** - N+1 prevention via max depth
- **Environment**: `FRAISEQL_DISABLE_RUST=1` - Disable Rust optimization

---

## PHASE 8 IMPLICATIONS: What to Measure for FraiseQL

### Key Metrics

**Query Generation Efficiency**:
- WhereType compilation time (should be <1ms per query)
- Cache hit ratio for compiled WHERE clauses
- Memory overhead of type system

**Execution Pipeline**:
- Rust vectorization benefit (measure response time with/without)
- JSONB → HTTP conversion time
- Null response caching effectiveness (compare to full parsing)

**Connection Pool**:
- Active/idle ratio by workload type
- Overflow connection usage (should be <10% during sustained load)
- Pool saturation point and latency degradation

**Caching**:
- PostgreSQL UNLOGGED table hit ratio
- Domain version invalidation frequency
- TTL cache effectiveness

**Performance by Workload**:
- **Simple (ping)**: <5ms p99, 1000+ req/sec
- **Parameterized**: <100ms p99, 200+ req/sec
- **Aggregation**: <200ms p99, 50+ req/sec
- **Pagination (offset)**: Degradation visible at page 100+
- **Pagination (cursor)**: Consistent <50ms regardless of offset
- **Full-text search**: <150ms p99 with GIN index
- **Deep traversal**: <300ms p99, 3-5 queries (vs 20+ without TV tables)
- **Mutations**: <200ms p99 with transaction handling

---

## COMPARISON: FraiseQL vs Other Frameworks

| Feature | FraiseQL | Strawberry | Graphene | FastAPI-REST |
|---------|----------|-----------|----------|--------------|
| **Architecture** | Rust-first | Pure Python | Pure Python | FastAPI |
| **Query auto-gen** | Yes (WhereType) | No | Partial | No |
| **N+1 prevention** | DataLoaders + TV | DataLoaders | None | Manual |
| **RBAC** | Built-in | No | No | Manual |
| **Audit logging** | Built-in | No | No | Manual |
| **Performance** | Rust pipeline | Python | Python | FastAPI |
| **Expected RPS** | 400-600 | 200-300 | 100-200 | 300-400 |
| **Array operators** | Yes (6 types) | No | No | No |
| **Vector search** | Yes (pgvector) | No | No | No |
| **Network types** | Yes (CIDR, IPv4/6) | No | No | No |
| **FTS operators** | Yes (ranking) | No | No | No |
| **Scalar types** | 57+ | ~20 | ~15 | N/A |
| **Multi-tenancy** | Built-in | No | No | Manual |
| **Enterprise ready** | Yes | No | No | No |

---

## SUMMARY: FraiseQL Capability Matrix

| Category | Capability Count | Status |
|----------|-----------------|--------|
| GraphQL Operations | 3 (Query, Mutation, Subscription) | ✅ Complete |
| Database Features | 8 (JSONB, arrays, vectors, FTS, network, dates, macaddr, ranges) | ✅ Complete |
| Security | 11 (Auth, RBAC, field auth, rate limit, CSRF, audit, encryption, etc.) | ✅ Enterprise |
| Performance | 5 (Rust pipeline, caching, DataLoader, N+1 detection, complexity) | ✅ Advanced |
| Auto-Generation | 6 (WHERE, ORDER BY, mutations, queries, types, inputs) | ✅ Comprehensive |
| Enterprise | 7 (Multi-tenancy, CQRS, IVM, migrations, audit, SBOM, etc.) | ✅ Ready |
| Integration | 6 (FastAPI, APQ, middleware, auto-discovery, LangChain, tracing) | ✅ Complete |
| Data | 4 (57+ scalars, pagination, partial instantiation, validation) | ✅ Rich |
| Schema | 5 (Modular composition, auto-discovery, validation, introspection) | ✅ Flexible |
| Development | 4 (CLI, debug mode, schema validation, error handling) | ✅ Comprehensive |

**Total Built-in Capabilities**: 59+

---

## Key Architectural Strengths

1. **Rust-first performance** - Zero Python JSON overhead
2. **PostgreSQL-native** - Leverages database strengths
3. **Convention-based** - Minimal configuration needed
4. **Enterprise features** - RBAC, audit, multi-tenancy included
5. **Type safety** - Compile-time GraphQL generation
6. **Extensibility** - Custom operators, scalars, middleware
7. **Production-ready** - Used in enterprise deployments
8. **Comprehensive** - One framework for everything

---

## For Phase 8 Monitoring

FraiseQL's comprehensive auto-generation means Phase 8 should focus on:

1. **Rust pipeline efficiency** - How fast is WhereType compilation?
2. **Connection pool behavior** - Is async pooling effective?
3. **Caching effectiveness** - Are UNLOGGED tables being used?
4. **Memory efficiency** - Partial instantiation reducing overhead?
5. **Query execution** - DataLoader N+1 prevention working?

Unlike other frameworks, you won't measure "did it implement aggregation correctly" (it's auto-generated). Instead, measure "how efficiently does it execute the auto-generated aggregation queries at scale?"

