import "reflect-metadata";
import express from "express";
import { createConnection } from "typeorm";
import { User } from "./entities/User.js";
import { Post } from "./entities/Post.js";
import { Comment } from "./entities/Comment.js";
import { createRoutes } from "./routes/index.js";

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

    // Create Express app
    const app = express();
    app.use(express.json());

    // Create routes with repositories
    const routes = createRoutes(
        connection.getRepository(User),
        connection.getRepository(Post),
        connection.getRepository(Comment)
    );

    // Use routes
    app.use("/api", routes);

    // Health check endpoint
    app.get("/health", (req, res) => {
        res.json({
            status: "UP",
            service: "express-orm-optimized-benchmark",
            optimization: "Eager loading prevents N+1 queries"
        });
    });

    // Start server
    const PORT = process.env.PORT || 8008;
    app.listen(PORT, () => {
        console.log(`🚀 Optimized Express ORM server ready at http://localhost:${PORT}`);
        console.log(`⚡ Eager loading enabled - no N+1 queries!`);
        console.log(`📍 API endpoints available at /api/*`);
    });
}

main().catch(console.error);