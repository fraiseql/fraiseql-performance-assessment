# Java Spring Boot REST & GraphQL Implementation Plan

## 📋 Overview

Implement comprehensive Java/Spring Boot benchmarking frameworks to establish JVM performance baseline, demonstrate GC characteristics, and provide enterprise-standard API patterns for comparison with other languages.

---

## 🎯 Objectives

1. **Implement Spring Boot REST API** - Enterprise standard REST patterns
2. **Implement Spring GraphQL** - Official Spring GraphQL support
3. **Establish JVM performance baseline** - Show GC/JIT warmup effects
4. **Demonstrate managed memory model** - Different from Rust/Go
5. **Provide enterprise hiring intelligence** - Answer "Is Spring slow?"
6. **Enable Java vs other language comparison** - Performance multipliers

---

## 📊 Scope

### What's Included

- ✅ Spring Boot 3.x REST API (5 endpoints)
- ✅ Spring for GraphQL (7 query fields)
- ✅ JPA/Hibernate ORM for relationship loading
- ✅ Connection pooling (HikariCP)
- ✅ Prometheus metrics collection
- ✅ Health checks and actuator endpoints
- ✅ Docker container with multi-stage build
- ✅ GC monitoring and heap analysis
- ✅ JVM tuning parameters for benchmarking

### What's NOT Included

- ❌ Quarkus (native compilation - separate framework)
- ❌ Micronaut (alternative lightweight framework)
- ❌ Reactive stack (Project Reactor - different paradigm)
- ❌ Kubernetes/cloud specific features

---

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Framework** | Spring Boot | 3.2.x | Latest stable |
| **Build** | Maven | 3.9.x | Standard enterprise build |
| **Language** | Java | 21 LTS | Latest LTS, virtual threads support |
| **REST** | Spring MVC | 6.x | Standard REST framework |
| **GraphQL** | Spring for GraphQL | 1.2.x | Official Spring GraphQL |
| **ORM** | JPA/Hibernate | 6.x | Standard Java ORM |
| **Connection Pool** | HikariCP | 5.x | Industry standard |
| **Metrics** | Micrometer + Prometheus | Latest | Spring default |
| **Database Driver** | PostgreSQL JDBC | 42.x | Type 4 driver |
| **Base Image** | Eclipse Temurin | 21-jdk-alpine | Official Java image |

### Project Structure

```
frameworks/java-spring-boot/
├── pom.xml                              # Maven configuration
├── src/main/java/com/fraiseql/
│   ├── FraiseqlApplication.java         # Main application class
│   ├── config/
│   │   ├── DatabaseConfig.java          # Connection pool config
│   │   ├── GraphQLConfig.java           # GraphQL schema setup
│   │   └── MetricsConfig.java           # Prometheus metrics
│   ├── models/
│   │   ├── User.java                    # JPA entity
│   │   ├── Post.java                    # JPA entity
│   │   └── Comment.java                 # JPA entity
│   ├── repositories/
│   │   ├── UserRepository.java          # Spring Data JPA
│   │   ├── PostRepository.java
│   │   └── CommentRepository.java
│   ├── services/
│   │   ├── UserService.java             # Business logic
│   │   ├── PostService.java
│   │   └── CommentService.java
│   ├── rest/
│   │   ├── UserController.java          # REST endpoints
│   │   ├── PostController.java
│   │   └── HealthController.java
│   └── graphql/
│       ├── UserGraphQL.java             # GraphQL resolvers
│       ├── PostGraphQL.java
│       └── CommentGraphQL.java
├── src/main/resources/
│   ├── application.yaml                 # Spring configuration
│   ├── graphql/schema.graphqls          # GraphQL schema definition
│   └── logback-spring.xml               # Logging configuration
├── Dockerfile                           # Multi-stage build
└── docker-entrypoint.sh                 # Container startup script
```

---

## 📝 Implementation Phases (10 phases, ~40 hours)

### Phase 1: Project Setup & Maven Configuration
**Objective**: Create Maven project with Spring Boot dependencies
**Duration**: 2-3 hours

**Tasks**:
1. Initialize Maven project structure
   ```bash
   mvn archetype:generate -DgroupId=com.fraiseql \
     -DartifactId=spring-boot-benchmark \
     -DarchetypeArtifactId=maven-archetype-quickstart
   ```

2. Add Spring Boot parent POM
   ```xml
   <parent>
       <groupId>org.springframework.boot</groupId>
       <artifactId>spring-boot-starter-parent</artifactId>
       <version>3.2.0</version>
   </parent>
   ```

3. Add core dependencies
   - spring-boot-starter-web (REST)
   - spring-boot-starter-graphql (GraphQL)
   - spring-boot-starter-data-jpa (ORM)
   - spring-boot-starter-actuator (metrics)
   - postgresql driver
   - HikariCP
   - micrometer-registry-prometheus

4. Verify compilation
   ```bash
   mvn clean compile
   ```

**Deliverables**:
- ✅ Maven project structure created
- ✅ All dependencies resolve
- ✅ `mvn clean compile` succeeds

---

### Phase 2: JPA Entities & Data Models
**Objective**: Define database models using JPA annotations
**Duration**: 2-3 hours

**Tasks**:
1. Create User entity
   ```java
   @Entity
   @Table(name = "tb_user", schema = "benchmark")
   @Getter @Setter @NoArgsConstructor
   public class User {
       @Id
       @Column(length = 36)
       private String id;

       @Column(nullable = false, unique = true)
       private String username;

       @Column(name = "first_name", nullable = false)
       private String firstName;

       @Column(name = "last_name", nullable = false)
       private String lastName;

       @Column(columnDefinition = "TEXT")
       private String bio;

       @OneToMany(mappedBy = "author", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
       private List<Post> posts;

       @OneToMany(mappedBy = "author", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
       private List<Comment> comments;
   }
   ```

2. Create Post entity with relationships
3. Create Comment entity with relationships
4. Add proper fetch strategies (EAGER for main queries, LAZY for relationships)

**Deliverables**:
- ✅ All 3 entities defined
- ✅ Relationships configured correctly
- ✅ Annotations compile without errors

---

### Phase 3: Spring Data Repositories
**Objective**: Create repository interfaces for database access
**Duration**: 1-2 hours

**Tasks**:
1. Create UserRepository extending JpaRepository
   ```java
   @Repository
   public interface UserRepository extends JpaRepository<User, String> {
       List<User> findAll(Pageable pageable);
   }
   ```

2. Create PostRepository with custom queries
   ```java
   @Repository
   public interface PostRepository extends JpaRepository<Post, String> {
       List<Post> findByAuthorId(String authorId, Pageable pageable);

       @Query("SELECT p FROM Post p LEFT JOIN FETCH p.author " +
              "WHERE p.id = :id")
       Optional<Post> findByIdWithAuthor(@Param("id") String id);
   }
   ```

3. Create CommentRepository
4. Add custom query methods with proper fetch strategies

**Deliverables**:
- ✅ All repositories defined
- ✅ Custom queries with FETCH JOIN avoid N+1
- ✅ Compile without errors

---

### Phase 4: REST Controllers
**Objective**: Implement 5 REST endpoints
**Duration**: 3-4 hours

**Tasks**:
1. Create UserController with endpoints
   - GET /api/users/{id}
   - GET /api/users?page=0&size=10
   - GET /api/health

2. Create PostController with endpoints
   - GET /api/posts/{id}
   - GET /api/posts?page=0&size=10

3. Implement response DTOs
4. Add proper error handling (ExceptionHandler, HTTP status codes)
5. Add request logging

**Example**:
```java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserDTO> getUser(@PathVariable String id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping
    public ResponseEntity<Page<UserDTO>> listUsers(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {

        Pageable pageable = PageRequest.of(page, size);
        return ResponseEntity.ok(userService.findAll(pageable));
    }
}
```

**Deliverables**:
- ✅ 5 REST endpoints working
- ✅ Proper HTTP status codes (200, 404, 500)
- ✅ JSON serialization working
- ✅ Error handling implemented

---

### Phase 5: Service Layer & Business Logic
**Objective**: Implement service layer with transaction management
**Duration**: 2-3 hours

**Tasks**:
1. Create UserService
   ```java
   @Service
   @RequiredArgsConstructor
   public class UserService {
       private final UserRepository userRepository;

       @Transactional(readOnly = true)
       public Optional<UserDTO> findById(String id) {
           return userRepository.findById(id)
               .map(this::toDTO);
       }

       @Transactional(readOnly = true)
       public Page<UserDTO> findAll(Pageable pageable) {
           return userRepository.findAll(pageable)
               .map(this::toDTO);
       }

       private UserDTO toDTO(User user) {
           // Convert entity to DTO
       }
   }
   ```

2. Create PostService with relationship loading
3. Create CommentService
4. Add transaction management with @Transactional
5. Add logging for monitoring

**Deliverables**:
- ✅ All services implemented
- ✅ Transaction management working
- ✅ DTO conversion functional

---

### Phase 6: Spring for GraphQL Implementation
**Objective**: Implement GraphQL queries using Spring for GraphQL
**Duration**: 4-5 hours

**Tasks**:
1. Create GraphQL schema (graphql/schema.graphqls)
   ```graphql
   type User {
       id: ID!
       username: String!
       firstName: String!
       lastName: String!
       bio: String
       posts: [Post!]!
       comments: [Comment!]!
   }

   type Post {
       id: ID!
       title: String!
       content: String
       author: User!
       comments: [Comment!]!
       createdAt: String!
   }

   type Comment {
       id: ID!
       content: String!
       post: Post!
       author: User!
       createdAt: String!
   }

   type Query {
       user(id: ID!): User
       users(first: Int, after: String): [User!]!
       post(id: ID!): Post
       posts(first: Int, after: String): [Post!]!
       postsByUser(userId: ID!, first: Int): [Post!]!
       commentsByPost(postId: ID!, first: Int): [Comment!]!
   }
   ```

2. Create GraphQL controllers/resolvers
   ```java
   @Controller
   @RequiredArgsConstructor
   public class UserGraphQL {
       private final UserService userService;

       @QueryMapping
       public UserDTO user(@Argument String id) {
           return userService.findById(id).orElse(null);
       }

       @QueryMapping
       public List<UserDTO> users(@Argument int first) {
           return userService.findAll(PageRequest.of(0, first))
               .getContent();
       }
   }
   ```

3. Implement relationship resolvers (posts, comments)
4. Add field resolution metrics

**Deliverables**:
- ✅ GraphQL schema defined and valid
- ✅ All 7 query fields implemented
- ✅ Relationships resolve correctly
- ✅ GraphQL endpoint working

---

### Phase 7: Prometheus Metrics & Monitoring
**Objective**: Add Prometheus metrics for performance monitoring
**Duration**: 2-3 hours

**Tasks**:
1. Configure Micrometer with Spring Boot Actuator
   ```yaml
   management:
     endpoints:
       web:
         exposure:
           include: health,metrics,prometheus
     metrics:
       tags:
         application: spring-boot-rest
   ```

2. Add custom metrics
   - REST request count/latency
   - GraphQL query count/latency
   - Database connection pool stats
   - JVM metrics (GC, heap, threads)

3. Expose `/actuator/prometheus` endpoint

**Deliverables**:
- ✅ /actuator/health returns status
- ✅ /actuator/metrics lists all metrics
- ✅ /actuator/prometheus returns Prometheus format
- ✅ Custom metrics collected

---

### Phase 8: Application Configuration & Startup
**Objective**: Configure Spring Boot application and startup
**Duration**: 2-3 hours

**Tasks**:
1. Create application.yaml
   ```yaml
   spring:
     application:
       name: fraiseql-spring-boot
     datasource:
       url: jdbc:postgresql://${DB_HOST:localhost}:${DB_PORT:5434}/${DB_NAME:fraiseql_benchmark}
       username: ${DB_USER:benchmark}
       password: ${DB_PASSWORD:benchmark123}
       hikari:
         minimum-idle: 20
         maximum-pool-size: 100
         connection-timeout: 10000
     jpa:
       hibernate:
         ddl-auto: validate
       properties:
         hibernate:
           jdbc:
             batch_size: 20
           order_inserts: true
           order_updates: true
   logging:
     level:
       org.springframework.web: INFO
       com.zaxxer.hikari: DEBUG
   ```

2. Configure embedded Tomcat
3. Set up application startup logging
4. Implement graceful shutdown

**Deliverables**:
- ✅ Application starts on port 8007
- ✅ Database connects successfully
- ✅ All endpoints responsive
- ✅ Metrics accessible

---

### Phase 9: Docker Container & Deployment
**Objective**: Create production-ready Docker image
**Duration**: 2-3 hours

**Tasks**:
1. Create multi-stage Dockerfile
   ```dockerfile
   # Stage 1: Build
   FROM maven:3.9-eclipse-temurin-21-alpine AS builder
   WORKDIR /app
   COPY pom.xml .
   RUN mvn dependency:resolve
   COPY src src
   RUN mvn clean package -DskipTests

   # Stage 2: Runtime
   FROM eclipse-temurin:21-jdk-alpine
   RUN apk add --no-cache curl
   COPY --from=builder /app/target/*.jar app.jar

   ENV JAVA_OPTS="-XX:+UseG1GC -XX:MaxGCPauseMillis=200 -Xms512m -Xmx1024m"
   EXPOSE 8007
   ENTRYPOINT exec java $JAVA_OPTS -jar app.jar
   ```

2. Build and test image
3. Optimize image size
4. Add health check

**Deliverables**:
- ✅ Docker image builds successfully
- ✅ Image runs and starts application
- ✅ Image size reasonable (~500MB)
- ✅ Health check working

---

### Phase 10: Docker Compose & Integration
**Objective**: Integrate into benchmarking suite
**Duration**: 2-3 hours

**Tasks**:
1. Add to docker-compose.yml
   ```yaml
   spring-boot:
     build: ./frameworks/java-spring-boot
     ports:
       - "8007:8007"
     depends_on:
       postgres:
         condition: service_healthy
     environment:
       - DB_HOST=postgres
       - DB_PORT=5432
       - DB_NAME=fraiseql_benchmark
       - DB_USER=benchmark
       - DB_PASSWORD=benchmark123
       - JAVA_OPTS=-XX:+UseG1GC -XX:MaxGCPauseMillis=200
     healthcheck:
       test: ["CMD", "curl", "-f", "http://localhost:8007/actuator/health"]
       interval: 30s
       timeout: 15s
       retries: 3
     networks:
       - fraiseql-benchmark
   ```

2. Update test script to recognize Spring Boot
3. Run full integration tests

**Deliverables**:
- ✅ Service in docker-compose.yml
- ✅ Service starts with stack
- ✅ Health checks pass
- ✅ Tests can connect and query

---

## 📋 Acceptance Criteria

### Phase Completion Gates

| Phase | Acceptance Criteria |
|-------|-------------------|
| 1 | `mvn clean compile` succeeds, no dependency conflicts |
| 2 | All 3 JPA entities compile, relationships configured |
| 3 | All repositories functional, custom queries work |
| 4 | 5 REST endpoints respond with correct HTTP status codes |
| 5 | Service layer transactional, DTOs serialize correctly |
| 6 | GraphQL schema valid, all 7 queries execute |
| 7 | Prometheus endpoint returns valid metrics |
| 8 | Application starts on port 8007, all endpoints accessible |
| 9 | Docker image builds and runs without errors |
| 10 | docker-compose up starts service successfully |

---

## 🎯 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **P50 Latency** | 20-25ms | REST, includes JVM warmup |
| **P99 Latency** | 50-80ms | After warmup, GC pauses visible |
| **Throughput** | 2000-3000 req/s | Per thread/core |
| **Memory** | 512-1024MB | Heap configured for benchmarking |
| **Startup Time** | 5-8 seconds | Java startup overhead |
| **Docker Image Size** | < 600MB | With JDK |

---

## 📊 Expected Performance Story

**What Spring Boot will demonstrate:**
- JVM warmup effect (latency improves over time)
- GC pause impact (visible in p99 latency)
- Thread-based concurrency overhead
- Connection pool benefits
- How managed memory differs from unmanaged (Rust/C)

**Comparison points:**
- vs Rust (Actix): ~3x slower (20-25ms vs 8-15ms)
- vs Go: ~2x slower (20-25ms vs 10-15ms)
- vs Python: Similar or faster (96ms vs 20-25ms)
- vs Node.js: Comparable (15-25ms each)

---

## 🔧 Development Commands

```bash
# Build
mvn clean package

# Run locally
mvn spring-boot:run

# Run tests
mvn test

# Build Docker image
docker build -t fraiseql-spring-boot .

# Run in container
docker run -e DB_HOST=host.docker.internal \
  -p 8007:8007 fraiseql-spring-boot
```

---

## 📚 References

- Spring Boot Docs: https://spring.io/projects/spring-boot
- Spring for GraphQL: https://spring.io/projects/spring-graphql
- Spring Data JPA: https://spring.io/projects/spring-data-jpa
- Hibernate Documentation: https://hibernate.org/

---

## ✅ Implementation Checklist

- [ ] Phase 1: Maven setup
- [ ] Phase 2: JPA entities
- [ ] Phase 3: Repositories
- [ ] Phase 4: REST controllers
- [ ] Phase 5: Service layer
- [ ] Phase 6: GraphQL implementation
- [ ] Phase 7: Prometheus metrics
- [ ] Phase 8: Application config
- [ ] Phase 9: Docker container
- [ ] Phase 10: Integration & testing

---

**Version**: 1.0 | **Status**: Ready for Implementation | **Estimated Hours**: 40
