import "reflect-metadata";
import express from "express";
import { createConnection } from "typeorm";
import { User } from "./entities/User";
import { Post } from "./entities/Post";
import { Comment } from "./entities/Comment";
import { createRoutes } from "./routes/index";

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
        res.json({ status: "healthy" });
    });

    // Start server
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
        console.log(`🚀 Naive Express ORM server ready at http://localhost:${PORT}`);
        console.log(`📊 Query logging enabled - watch for N+1 patterns!`);
        console.log(`📍 API endpoints available at /api/*`);
    });
}

main().catch(console.error);