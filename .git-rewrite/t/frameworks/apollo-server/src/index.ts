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
