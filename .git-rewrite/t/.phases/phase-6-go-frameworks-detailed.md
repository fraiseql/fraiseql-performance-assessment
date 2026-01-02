# FraiseQL Performance Assessment - Phase 6: Go Framework Implementations

## Phase Overview

**Goal**: Implement gqlgen (GraphQL) and Gin (REST) frameworks in Go, showcasing true concurrency without GIL limitations, compiled performance, and production-grade connection pooling with pgx.

**Scope**: Add Go frameworks to demonstrate compiled language performance advantages over interpreted Python/Node.js.

**Success Criteria**:
- gqlgen starts and responds to GraphQL queries
- Gin REST implements equivalent endpoints
- DataLoader batches related entity lookups
- pgxpool configured (min 10, max 100 connections)
- Compiled binaries < 20MB each
- Throughput significantly higher than Python equivalents

## Learning Objectives

As a junior engineer, by completing Phase 6 you will learn:

1. **Node.js Production Patterns**: Async/await, connection pooling, error handling
2. **GraphQL Implementation**: Apollo Server setup, schema design, resolver patterns
3. **DataLoader Patterns**: N+1 prevention, batch loading, caching strategies
4. **TypeScript Development**: Type safety, interfaces, compilation
5. **REST API Design**: Express routing, middleware, request handling
6. **JavaScript Tooling**: npm, package.json, build processes
7. **Cross-Language Comparison**: Performance characteristics vs Python

## Prerequisites and Knowledge Requirements

### Required Knowledge
- JavaScript/TypeScript async/await patterns
- Basic GraphQL concepts
- REST API design principles
- npm package management

### Required Tools
- Node.js 20+, npm, TypeScript
- PostgreSQL pg library
- Apollo Server, Express, DataLoader

## Implementation Steps

### Step 1: Apollo Server Project Setup
**Estimated Time**: 1 hour

```json
// frameworks/apollo-server/package.json
{
  "name": "apollo-benchmark",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@apollo/server": "^4.10.0",
    "graphql": "^16.8.0",
    "dataloader": "^2.2.0",
    "pg": "^8.11.0",
    "prom-client": "^15.1.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/pg": "^8.10.0",
    "typescript": "^5.3.0",
    "tsx": "^4.7.0"
  }
}
```

### Step 2: Database Connection Pool
**Estimated Time**: 45 minutes

```typescript
// frameworks/apollo-server/src/db.ts
import pg from 'pg';
const { Pool } = pg;

export const pool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'fraiseql_benchmark',
  user: process.env.DB_USER || 'benchmark',
  password: process.env.DB_PASSWORD || 'benchmark123',
  min: 10,
  max: 50,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});
```

### Step 3: DataLoader Implementation
**Estimated Time**: 1 hour

```typescript
// frameworks/apollo-server/src/dataloaders.ts
import DataLoader from 'dataloader';

export function createDataLoaders() {
  return {
    userLoader: new DataLoader(async (ids) => {
      const query = `SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = ANY($1)`;
      const result = await pool.query(query, [ids]);
      const userMap = new Map(result.rows.map(u => [u.id, u]));
      return ids.map(id => userMap.get(id) || null);
    }),
    
    postsByAuthorLoader: new DataLoader(async (authorIds) => {
      const query = `SELECT id, author_id, title, content FROM benchmark.posts WHERE author_id = ANY($1) AND status = 'published' ORDER BY created_at DESC`;
      const result = await pool.query(query, [authorIds]);
      const postMap = new Map();
      result.rows.forEach(post => {
        if (!postMap.has(post.author_id)) postMap.set(post.author_id, []);
        postMap.get(post.author_id).push(post);
      });
      return authorIds.map(id => postMap.get(id) || []);
    }),
  };
}
```

### Step 4: GraphQL Schema & Resolvers
**Estimated Time**: 1.5 hours

```typescript
// frameworks/apollo-server/src/schema.ts
export const typeDefs = `#graphql
  type User {
    id: ID!
    username: String!
    firstName: String
    lastName: String
    bio: String
    posts(limit: Int = 10): [Post!]!
  }
  
  type Post {
    id: ID!
    title: String!
    content: String
    author: User!
  }
  
  type Query {
    ping: String!
    user(id: ID!): User
    users(limit: Int = 10): [User!]!
    post(id: ID!): Post
    posts(limit: Int = 10): [Post!]!
  }
`;
```

```typescript
// frameworks/apollo-server/src/resolvers.ts
export const resolvers = {
  Query: {
    ping: () => 'pong',
    user: async (_: any, { id }: { id: string }, { loaders }: any) => {
      return loaders.userLoader.load(id);
    },
    users: async (_: any, { limit }: { limit: number }) => {
      const query = `SELECT id, username, first_name, last_name, bio FROM benchmark.users ORDER BY created_at DESC LIMIT $1`;
      const result = await pool.query(query, [limit]);
      return result.rows;
    },
    posts: async (_: any, { limit }: { limit: number }) => {
      const query = `SELECT id, author_id, title, content FROM benchmark.posts WHERE status = 'published' ORDER BY created_at DESC LIMIT $1`;
      const result = await pool.query(query, [limit]);
      return result.rows;
    },
  },
  
  User: {
    firstName: (user: any) => user.first_name,
    lastName: (user: any) => user.last_name,
    posts: async (user: any, { limit }: { limit: number }, { loaders }: any) => {
      const posts = await loaders.postsByAuthorLoader.load(user.id);
      return posts.slice(0, limit);
    },
  },
  
  Post: {
    author: async (post: any, _: any, { loaders }: any) => {
      return loaders.userLoader.load(post.author_id);
    },
  },
};
```

### Step 5: Apollo Server Entry Point
**Estimated Time**: 45 minutes

```typescript
// frameworks/apollo-server/src/index.ts
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { collectDefaultMetrics, Counter } from 'prom-client';
import http from 'http';
import { typeDefs } from './schema.js';
import { resolvers } from './resolvers.js';
import { createDataLoaders } from './dataloaders.js';
import { pool } from './db.js';

// Metrics setup
collectDefaultMetrics();
const requestCounter = new Counter({
  name: 'apollo_requests_total',
  help: 'Total GraphQL requests',
});

const server = new ApolloServer({ typeDefs, resolvers });

const { url } = await startStandaloneServer(server, {
  listen: { port: 4001 },
  context: async () => ({
    loaders: createDataLoaders(),
  }),
});

console.log(`🚀 Apollo Server ready at ${url}`);

// Health endpoint
const metricsServer = http.createServer(async (req, res) => {
  if (req.url === '/health') {
    try {
      await pool.query('SELECT 1');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'healthy', framework: 'apollo-server' }));
    } catch (error) {
      res.writeHead(503);
      res.end(JSON.stringify({ status: 'unhealthy', error: String(error) }));
    }
  }
});

metricsServer.listen(4002);
```

### Step 6: Express REST Implementation
**Estimated Time**: 1 hour

```typescript
// frameworks/express-rest/src/index.ts
import express from 'express';
import { collectDefaultMetrics } from 'prom-client';
import { pool } from './db.js';

const app = express();
app.use(express.json());

collectDefaultMetrics();

app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'healthy', framework: 'express-rest' });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: String(error) });
  }
});

app.get('/users', async (req, res) => {
  const limit = parseInt(req.query.limit as string) || 10;
  const result = await pool.query(
    `SELECT id, username, first_name, last_name, bio FROM benchmark.users ORDER BY created_at DESC LIMIT $1`,
    [limit]
  );
  res.json(result.rows);
});

app.get('/users/:id', async (req, res) => {
  const { id } = req.params;
  const include = (req.query.include as string || '').split(',');
  
  const userResult = await pool.query(
    `SELECT id, username, first_name, last_name, bio FROM benchmark.users WHERE id = $1`,
    [id]
  );
  
  if (userResult.rows.length === 0) {
    return res.status(404).json({ error: 'User not found' });
  }
  
  const user = userResult.rows[0];
  const result: any = { ...user, first_name: user.first_name, last_name: user.last_name };
  
  if (include.includes('posts')) {
    const postsResult = await pool.query(
      `SELECT id, title, content FROM benchmark.posts WHERE author_id = $1 AND status = 'published' ORDER BY created_at DESC LIMIT 10`,
      [id]
    );
    result.posts = postsResult.rows;
  }
  
  res.json(result);
});

const PORT = parseInt(process.env.PORT || '8005');
app.listen(PORT, () => {
  console.log(`🚀 Express REST server ready at http://localhost:${PORT}`);
});
```

## Testing Strategy

### Functionality Testing
- GraphQL query execution and response validation
- REST endpoint responses and error handling
- DataLoader batching verification
- Connection pool operation

### Performance Testing
- Throughput comparison with Python frameworks
- Memory usage and garbage collection patterns
- Event loop blocking detection

## Best Practices Learned

### 1. Node.js Async Patterns
- Always use async/await for database operations
- Implement proper error handling in async functions
- Use connection pooling for database efficiency
- Monitor event loop performance

### 2. GraphQL Implementation
- Use DataLoader for N+1 query prevention
- Implement proper resolver patterns
- Handle errors gracefully in resolvers
- Use TypeScript for type safety

### 3. REST API Design
- Implement consistent error responses
- Use middleware for common functionality
- Validate input parameters
- Provide comprehensive health checks

## Phase Sign-off

**Phase 5 Status**: ☐ Ready for Phase 6 ☐ Needs Remediation

**Frameworks Implemented**:
- Apollo Server (GraphQL) - TypeScript, DataLoader, connection pooling
- Express REST - TypeScript, middleware, error handling

**Performance Validations**:
- DataLoader prevents N+1 queries
- Connection pools properly configured
- TypeScript compilation successful</content>
<parameter name="filePath">.phases/phase-5-nodejs-frameworks-detailed.md