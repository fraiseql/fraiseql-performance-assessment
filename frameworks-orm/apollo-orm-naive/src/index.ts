import "reflect-metadata";
import { ApolloServer } from "apollo-server-express";
import express from "express";
import { createConnection } from "typeorm";
import { buildSchema } from "type-graphql";
import { UserResolver, PostResolver } from "./resolvers/index";
import { User } from "./entities/User";
import { Post } from "./entities/Post";
import { Comment } from "./entities/Comment";

async function main() {
    // Create TypeORM connection
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
        logging: true, // Log all queries to show N+1!
    });

    // Build GraphQL schema with naive resolvers
    const schema = await buildSchema({
        resolvers: [UserResolver, PostResolver],
        // No global middlewares for naive implementation
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
    server.applyMiddleware({ app: app as any });

    // Health check endpoint
    app.get("/health", (req, res) => {
        res.json({ status: "healthy" });
    });

    // Start server
    const PORT = process.env.PORT || 4000;
    app.listen(PORT, () => {
        console.log(`🚀 Naive Apollo ORM server ready at http://localhost:${PORT}${server.graphqlPath}`);
        console.log(`📊 Query logging enabled - watch for N+1 patterns!`);
    });
}

main().catch(console.error);