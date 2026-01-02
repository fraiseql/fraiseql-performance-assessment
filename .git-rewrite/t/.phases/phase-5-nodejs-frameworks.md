# Phase 5: Node.js Framework Implementations

## Objective

Implement Apollo Server (GraphQL) and Express (REST) frameworks with production-grade async patterns, connection pooling, and DataLoader for N+1 prevention comparison against Python frameworks.

## Context

**Current State:**
- Only Python frameworks implemented (5/11)
- No JavaScript/Node.js representation
- Cannot compare Python GIL limitations vs Node.js event loop
- Apollo Server is industry-standard GraphQL implementation

**Target State:**
- Apollo Server 4 with DataLoader batching
- Express REST with pg connection pool
- TypeScript for type safety
- Comparable feature parity with Python implementations
- Node.js clustering for multi-core utilization

## Files to Create

| File | Purpose |
|------|---------|
| `frameworks/apollo-server/` | Apollo Server GraphQL implementation |
| `frameworks/apollo-server/package.json` | Dependencies |
| `frameworks/apollo-server/tsconfig.json` | TypeScript config |
| `frameworks/apollo-server/src/index.ts` | Main entry point |
| `frameworks/apollo-server/src/schema.ts` | GraphQL schema |
| `frameworks/apollo-server/src/resolvers.ts` | Query resolvers |
| `frameworks/apollo-server/src/dataloaders.ts` | DataLoader instances |
| `frameworks/apollo-server/src/db.ts` | Database connection pool |
| `frameworks/apollo-server/Dockerfile` | Container build |
| `frameworks/express-rest/` | Express REST implementation |
| `frameworks/express-rest/package.json` | Dependencies |
| `frameworks/express-rest/src/index.ts` | Main entry point |
| `frameworks/express-rest/src/routes/` | REST endpoints |
| `frameworks/express-rest/src/db.ts` | Database pool |
| `frameworks/express-rest/Dockerfile` | Container build |

## Implementation Steps

### Step 1: Apollo Server Project Setup

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

```json
// frameworks/apollo-server/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

### Step 2: Database Connection Pool

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
  // Connection pool settings
  min: 10,
  max: 50,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
  // Statement caching
  statement_timeout: 30000,
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  await pool.end();
  process.exit(0);
});

export async function query<T = any>(text: string, params?: any[]): Promise<T[]> {
  const result = await pool.query(text, params);
  return result.rows as T[];
}

export async function queryOne<T = any>(text: string, params?: any[]): Promise<T | null> {
  const rows = await query<T>(text, params);
  return rows[0] || null;
}
```

### Step 3: DataLoader Implementation

```typescript
// frameworks/apollo-server/src/dataloaders.ts
import DataLoader from 'dataloader';
import { query } from './db.js';

interface User {
  id: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  bio: string | null;
}

interface Post {
  id: string;
  author_id: string;
  title: string;
  content: string | null;
  status: string;
}

interface Comment {
  id: string;
  post_id: string;
  author_id: string;
  content: string;
}

export function createDataLoaders() {
  return {
    // Batch load users by ID
    userLoader: new DataLoader<string, User | null>(async (ids) => {
      const users = await query<User>(
        `SELECT id, username, first_name, last_name, bio
         FROM benchmark.users
         WHERE id = ANY($1)`,
        [ids]
      );
      const userMap = new Map(users.map(u => [u.id, u]));
      return ids.map(id => userMap.get(id) || null);
    }),

    // Batch load posts by author ID
    postsByAuthorLoader: new DataLoader<string, Post[]>(async (authorIds) => {
      const posts = await query<Post>(
        `SELECT id, author_id, title, content, status
         FROM benchmark.posts
         WHERE author_id = ANY($1) AND status = 'published'
         ORDER BY created_at DESC`,
        [authorIds]
      );
      const postMap = new Map<string, Post[]>();
      for (const post of posts) {
        if (!postMap.has(post.author_id)) {
          postMap.set(post.author_id, []);
        }
        postMap.get(post.author_id)!.push(post);
      }
      return authorIds.map(id => postMap.get(id) || []);
    }),

    // Batch load comments by post ID
    commentsByPostLoader: new DataLoader<string, Comment[]>(async (postIds) => {
      const comments = await query<Comment>(
        `SELECT id, post_id, author_id, content
         FROM benchmark.comments
         WHERE post_id = ANY($1) AND is_approved = true
         ORDER BY created_at DESC`,
        [postIds]
      );
      const commentMap = new Map<string, Comment[]>();
      for (const comment of comments) {
        if (!commentMap.has(comment.post_id)) {
          commentMap.set(comment.post_id, []);
        }
        commentMap.get(comment.post_id)!.push(comment);
      }
      return postIds.map(id => commentMap.get(id) || []);
    }),

    // Batch load follower counts
    followerCountLoader: new DataLoader<string, number>(async (userIds) => {
      const counts = await query<{ following_id: string; count: string }>(
        `SELECT following_id, COUNT(*)::text as count
         FROM benchmark.user_follows
         WHERE following_id = ANY($1)
         GROUP BY following_id`,
        [userIds]
      );
      const countMap = new Map(counts.map(c => [c.following_id, parseInt(c.count)]));
      return userIds.map(id => countMap.get(id) || 0);
    }),
  };
}

export type DataLoaders = ReturnType<typeof createDataLoaders>;
```

### Step 4: GraphQL Schema & Resolvers

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
    followerCount: Int!
  }

  type Post {
    id: ID!
    title: String!
    content: String
    author: User!
    comments(limit: Int = 10): [Comment!]!
  }

  type Comment {
    id: ID!
    content: String!
    author: User!
    post: Post!
  }

  type Query {
    ping: String!
    user(id: ID!): User
    users(limit: Int = 10): [User!]!
    post(id: ID!): Post
    posts(limit: Int = 10): [Post!]!
    comment(id: ID!): Comment
    comments(limit: Int = 10): [Comment!]!
  }

  type Mutation {
    updateUser(id: ID!, firstName: String, lastName: String, bio: String): User
  }
`;
```

```typescript
// frameworks/apollo-server/src/resolvers.ts
import { query, queryOne } from './db.js';
import type { DataLoaders } from './dataloaders.js';

interface Context {
  loaders: DataLoaders;
}

export const resolvers = {
  Query: {
    ping: () => 'pong',

    user: async (_: any, { id }: { id: string }, { loaders }: Context) => {
      return loaders.userLoader.load(id);
    },

    users: async (_: any, { limit }: { limit: number }) => {
      return query(
        `SELECT id, username, first_name, last_name, bio
         FROM benchmark.users
         ORDER BY created_at DESC
         LIMIT $1`,
        [limit]
      );
    },

    post: async (_: any, { id }: { id: string }) => {
      return queryOne(
        `SELECT id, author_id, title, content, status
         FROM benchmark.posts
         WHERE id = $1`,
        [id]
      );
    },

    posts: async (_: any, { limit }: { limit: number }) => {
      return query(
        `SELECT id, author_id, title, content, status
         FROM benchmark.posts
         WHERE status = 'published'
         ORDER BY created_at DESC
         LIMIT $1`,
        [limit]
      );
    },
  },

  User: {
    firstName: (user: any) => user.first_name,
    lastName: (user: any) => user.last_name,

    posts: async (user: any, { limit }: { limit: number }, { loaders }: Context) => {
      const posts = await loaders.postsByAuthorLoader.load(user.id);
      return posts.slice(0, limit);
    },

    followerCount: async (user: any, _: any, { loaders }: Context) => {
      return loaders.followerCountLoader.load(user.id);
    },
  },

  Post: {
    author: async (post: any, _: any, { loaders }: Context) => {
      return loaders.userLoader.load(post.author_id);
    },

    comments: async (post: any, { limit }: { limit: number }, { loaders }: Context) => {
      const comments = await loaders.commentsByPostLoader.load(post.id);
      return comments.slice(0, limit);
    },
  },

  Comment: {
    author: async (comment: any, _: any, { loaders }: Context) => {
      return loaders.userLoader.load(comment.author_id);
    },
  },

  Mutation: {
    updateUser: async (_: any, args: any) => {
      const { id, firstName, lastName, bio } = args;
      const updates: string[] = [];
      const values: any[] = [];
      let paramIndex = 1;

      if (firstName !== undefined) {
        updates.push(`first_name = $${paramIndex++}`);
        values.push(firstName);
      }
      if (lastName !== undefined) {
        updates.push(`last_name = $${paramIndex++}`);
        values.push(lastName);
      }
      if (bio !== undefined) {
        updates.push(`bio = $${paramIndex++}`);
        values.push(bio);
      }

      if (updates.length > 0) {
        values.push(id);
        await query(
          `UPDATE benchmark.users
           SET ${updates.join(', ')}, updated_at = NOW()
           WHERE id = $${paramIndex}`,
          values
        );
      }

      return queryOne(
        `SELECT id, username, first_name, last_name, bio
         FROM benchmark.users WHERE id = $1`,
        [id]
      );
    },
  },
};
```

### Step 5: Apollo Server Entry Point

```typescript
// frameworks/apollo-server/src/index.ts
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { register, collectDefaultMetrics, Counter, Histogram } from 'prom-client';
import http from 'http';
import { typeDefs } from './schema.js';
import { resolvers } from './resolvers.js';
import { createDataLoaders } from './dataloaders.js';
import { pool } from './db.js';

// Prometheus metrics
collectDefaultMetrics();

const requestCounter = new Counter({
  name: 'apollo_requests_total',
  help: 'Total GraphQL requests',
  labelNames: ['operation'],
});

const requestDuration = new Histogram({
  name: 'apollo_request_duration_seconds',
  help: 'GraphQL request duration',
  labelNames: ['operation'],
});

// Create Apollo Server
const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [
    {
      async requestDidStart() {
        const start = Date.now();
        return {
          async willSendResponse(requestContext) {
            const duration = (Date.now() - start) / 1000;
            const operation = requestContext.operationName || 'unknown';
            requestCounter.inc({ operation });
            requestDuration.observe({ operation }, duration);
          },
        };
      },
    },
  ],
});

// Start server
const { url } = await startStandaloneServer(server, {
  listen: { port: 4001 },
  context: async () => ({
    loaders: createDataLoaders(),
  }),
});

console.log(`🚀 Apollo Server ready at ${url}`);

// Health & Metrics endpoints (separate HTTP server)
const metricsServer = http.createServer(async (req, res) => {
  if (req.url === '/health') {
    try {
      await pool.query('SELECT 1');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'healthy', framework: 'apollo-server' }));
    } catch (error) {
      res.writeHead(503, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'unhealthy', error: String(error) }));
    }
  } else if (req.url === '/metrics') {
    res.writeHead(200, { 'Content-Type': register.contentType });
    res.end(await register.metrics());
  } else {
    res.writeHead(404);
    res.end();
  }
});

metricsServer.listen(4002, () => {
  console.log('📊 Metrics server ready at http://localhost:4002');
});
```

### Step 6: Express REST Implementation

```typescript
// frameworks/express-rest/src/index.ts
import express from 'express';
import { register, collectDefaultMetrics, Counter, Histogram } from 'prom-client';
import { pool, query, queryOne } from './db.js';

const app = express();
app.use(express.json());

// Prometheus metrics
collectDefaultMetrics();
const requestCounter = new Counter({
  name: 'express_requests_total',
  help: 'Total REST requests',
  labelNames: ['method', 'path', 'status'],
});
const requestDuration = new Histogram({
  name: 'express_request_duration_seconds',
  help: 'REST request duration',
  labelNames: ['method', 'path'],
});

// Middleware for metrics
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    requestCounter.inc({ method: req.method, path: req.path, status: res.statusCode.toString() });
    requestDuration.observe({ method: req.method, path: req.path }, duration);
  });
  next();
});

// Health endpoint
app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'healthy', framework: 'express-rest' });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: String(error) });
  }
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.send(await register.metrics());
});

// Ping endpoint
app.get('/ping', (req, res) => {
  res.json({ message: 'pong' });
});

// Users endpoints
app.get('/users', async (req, res) => {
  const limit = parseInt(req.query.limit as string) || 10;
  const users = await query(
    `SELECT id, username, first_name, last_name, bio
     FROM benchmark.users
     ORDER BY created_at DESC
     LIMIT $1`,
    [limit]
  );
  res.json(users);
});

app.get('/users/:id', async (req, res) => {
  const { id } = req.params;
  const include = (req.query.include as string || '').split(',').filter(Boolean);

  const user = await queryOne(
    `SELECT id, username, first_name, last_name, bio
     FROM benchmark.users WHERE id = $1`,
    [id]
  );

  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  const result: any = { ...user };

  // Include relationships based on query parameter
  if (include.includes('posts')) {
    result.posts = await query(
      `SELECT id, title, content FROM benchmark.posts
       WHERE author_id = $1 AND status = 'published'
       ORDER BY created_at DESC LIMIT 10`,
      [id]
    );
  }

  if (include.includes('followers')) {
    const followers = await query(
      `SELECT u.id, u.username FROM benchmark.users u
       JOIN benchmark.user_follows f ON u.id = f.follower_id
       WHERE f.following_id = $1 LIMIT 10`,
      [id]
    );
    result.followers = followers;
  }

  if (include.includes('following')) {
    const following = await query(
      `SELECT u.id, u.username FROM benchmark.users u
       JOIN benchmark.user_follows f ON u.id = f.following_id
       WHERE f.follower_id = $1 LIMIT 10`,
      [id]
    );
    result.following = following;
  }

  res.json(result);
});

app.put('/users/:id', async (req, res) => {
  const { id } = req.params;
  const { firstName, lastName, bio } = req.body;

  const updates: string[] = [];
  const values: any[] = [];
  let paramIndex = 1;

  if (firstName !== undefined) {
    updates.push(`first_name = $${paramIndex++}`);
    values.push(firstName);
  }
  if (lastName !== undefined) {
    updates.push(`last_name = $${paramIndex++}`);
    values.push(lastName);
  }
  if (bio !== undefined) {
    updates.push(`bio = $${paramIndex++}`);
    values.push(bio);
  }

  if (updates.length > 0) {
    values.push(id);
    await query(
      `UPDATE benchmark.users
       SET ${updates.join(', ')}, updated_at = NOW()
       WHERE id = $${paramIndex}`,
      values
    );
  }

  const user = await queryOne(
    `SELECT id, username, first_name, last_name, bio
     FROM benchmark.users WHERE id = $1`,
    [id]
  );

  res.json(user);
});

// Posts endpoints
app.get('/posts', async (req, res) => {
  const limit = parseInt(req.query.limit as string) || 10;
  const include = (req.query.include as string || '').split(',').filter(Boolean);

  const posts = await query(
    `SELECT id, author_id, title, content, status
     FROM benchmark.posts
     WHERE status = 'published'
     ORDER BY created_at DESC
     LIMIT $1`,
    [limit]
  );

  if (include.includes('author')) {
    const authorIds = [...new Set(posts.map((p: any) => p.author_id))];
    const authors = await query(
      `SELECT id, username, first_name, last_name
       FROM benchmark.users WHERE id = ANY($1)`,
      [authorIds]
    );
    const authorMap = new Map(authors.map((a: any) => [a.id, a]));
    posts.forEach((p: any) => {
      p.author = authorMap.get(p.author_id);
    });
  }

  res.json(posts);
});

app.get('/posts/:id', async (req, res) => {
  const { id } = req.params;
  const include = (req.query.include as string || '').split(',').filter(Boolean);

  const post = await queryOne(
    `SELECT id, author_id, title, content, status
     FROM benchmark.posts WHERE id = $1`,
    [id]
  );

  if (!post) {
    return res.status(404).json({ error: 'Post not found' });
  }

  const result: any = { ...post };

  if (include.includes('author')) {
    result.author = await queryOne(
      `SELECT id, username, first_name, last_name
       FROM benchmark.users WHERE id = $1`,
      [post.author_id]
    );
  }

  if (include.includes('comments')) {
    result.comments = await query(
      `SELECT c.id, c.content, u.id as author_id, u.username as author_username
       FROM benchmark.comments c
       JOIN benchmark.users u ON c.author_id = u.id
       WHERE c.post_id = $1 AND c.is_approved = true
       ORDER BY c.created_at DESC LIMIT 20`,
      [id]
    );
  }

  res.json(result);
});

// Start server
const PORT = parseInt(process.env.PORT || '8005');
app.listen(PORT, () => {
  console.log(`🚀 Express REST server ready at http://localhost:${PORT}`);
});
```

### Step 7: Dockerfiles

```dockerfile
# frameworks/apollo-server/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY tsconfig.json ./
COPY src ./src
RUN npm run build

EXPOSE 4001 4002

CMD ["node", "dist/index.js"]
```

```dockerfile
# frameworks/express-rest/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY tsconfig.json ./
COPY src ./src
RUN npm run build

EXPOSE 8005

CMD ["node", "dist/index.js"]
```

### Step 8: Update Docker Compose

```yaml
# docker-compose.yml additions
apollo-server:
  build: ./frameworks/apollo-server
  ports:
    - "4001:4001"
    - "4002:4002"
  environment:
    - DB_HOST=postgres
    - DB_PORT=5432
    - DB_NAME=fraiseql_benchmark
    - DB_USER=benchmark
    - DB_PASSWORD=benchmark123
  depends_on:
    - postgres
  healthcheck:
    test: ["CMD", "wget", "-q", "--spider", "http://localhost:4002/health"]
    interval: 10s
    timeout: 5s
    retries: 5

express-rest:
  build: ./frameworks/express-rest
  ports:
    - "8005:8005"
  environment:
    - DB_HOST=postgres
    - DB_PORT=5432
    - DB_NAME=fraiseql_benchmark
    - DB_USER=benchmark
    - DB_PASSWORD=benchmark123
    - PORT=8005
  depends_on:
    - postgres
  healthcheck:
    test: ["CMD", "wget", "-q", "--spider", "http://localhost:8005/health"]
    interval: 10s
    timeout: 5s
    retries: 5
```

## Verification Commands

```bash
# Build and start Node.js services
docker-compose build apollo-server express-rest
docker-compose up -d apollo-server express-rest

# Test Apollo Server
curl -X POST http://localhost:4001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user(id: \"00000001-1111-1111-1111-111111111111\") { id username posts { title } } }"}'

# Test Express REST
curl "http://localhost:8005/users/00000001-1111-1111-1111-111111111111?include=posts,followers"

# Check health endpoints
curl http://localhost:4002/health
curl http://localhost:8005/health

# Check metrics
curl http://localhost:4002/metrics
curl http://localhost:8005/metrics

# Verify DataLoader batching (check query count in logs)
curl -X POST http://localhost:4001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ posts(limit: 10) { id title author { username } } }"}'
# Should batch all author lookups into single query
```

## Acceptance Criteria

- [ ] Apollo Server starts and responds to GraphQL queries
- [ ] Express REST starts and responds to REST endpoints
- [ ] DataLoader batches related entity lookups (N+1 prevention)
- [ ] Connection pools configured (min 10, max 50)
- [ ] Health endpoints respond with framework identification
- [ ] Prometheus metrics exported
- [ ] TypeScript compiles without errors
- [ ] Docker containers build and run successfully

## DO NOT

- Use synchronous database queries (blocks event loop)
- Create connections per request (no pooling)
- Skip DataLoader for relationship resolution
- Ignore graceful shutdown (connection leaks)
- Use CommonJS modules (use ES modules)

## Dependencies

```json
// Apollo Server
{
  "@apollo/server": "^4.10.0",
  "graphql": "^16.8.0",
  "dataloader": "^2.2.0",
  "pg": "^8.11.0",
  "prom-client": "^15.1.0"
}

// Express REST
{
  "express": "^4.18.0",
  "pg": "^8.11.0",
  "prom-client": "^15.1.0"
}
```

## Estimated Complexity

**Medium-High** - Requires TypeScript setup, DataLoader integration, and proper async patterns. Apollo Server 4 API is different from v3.
