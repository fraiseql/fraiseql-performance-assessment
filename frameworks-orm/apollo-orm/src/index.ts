import "reflect-metadata";
import { ApolloServer } from "apollo-server-express";
import express from "express";
import { createConnection } from "typeorm";
import { buildSchema } from "type-graphql";
import { UserResolver, PostResolver } from "./resolvers/index.js";
import { User } from "./entities/User.js";
import { Post } from "./entities/Post.js";
import { Comment } from "./entities/Comment.js";

async function main() {
    // Create TypeORM connection with optimized settings
    const connection = await createConnection({
        type: "postgres",
        host: process.env.DB_HOST || "postgres",
        port: parseInt(process.env.DB_PORT || "5432"),
        username: process.env.DB_USER || "benchmark",
        password: process.env.DB_PASSWORD || "benchmark123",
        database: process.env.DB_NAME || "fraiseql_benchmark",
        schema: "benchmark",
        entities: [User, Post, Comment],
        synchronize: false,
        logging: false, // OPTIMIZED: Disable logging for performance
        // OPTIMIZED: Connection pool settings for performance
        extra: {
            max: 20,
            min: 5,
            idleTimeoutMillis: 600000,
            acquireTimeoutMillis: 30000,
        }
    });

    // Build GraphQL schema with optimized resolvers
    const schema = await buildSchema({
        resolvers: [UserResolver, PostResolver],
        // OPTIMIZED: No global middlewares needed - relationships preloaded
    });

    // Create Express app
    const app = express();

    // Create Apollo Server
    const server = new ApolloServer({
        schema,
        context: () => ({
            userRepository: connection.getRepository(User),
            postRepository: connection.getRepository(Post),
            commentRepository: connection.getRepository(Comment),
        }),
    });

    // Start Apollo Server
    await server.start();

    // Apply middleware
    server.applyMiddleware({ app });

    // Health check endpoint
    app.get("/health", (req, res) => {
        res.json({
            status: "UP",
            service: "apollo-orm-optimized-benchmark",
            optimization: "Eager loading prevents N+1 queries"
        });
    });

    // Start server
    const PORT = process.env.PORT || 4002;
    app.listen(PORT, () => {
        console.log(`🚀 Optimized Apollo ORM server ready at http://localhost:${PORT}${server.graphqlPath}`);
        console.log(`⚡ Eager loading enabled - no N+1 queries!`);
        console.log(`📍 GraphQL playground at http://localhost:${PORT}${server.graphqlPath}`);
    });
}

main().catch(console.error);