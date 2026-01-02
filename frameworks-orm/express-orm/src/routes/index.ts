import express from "express";
import { Repository } from "typeorm";
import { User } from "../entities/User.js";
import { Post } from "../entities/Post.js";
import { Comment } from "../entities/Comment.js";

const router = express.Router();

export function createRoutes(
    userRepository: Repository<User>,
    postRepository: Repository<Post>,
    commentRepository: Repository<Comment>
) {
    // GET /users - Get all users (OPTIMIZED: eager loading relationships)
    router.get("/users", async (req, res) => {
        try {
            const limit = parseInt(req.query.limit as string) || 10;

            // OPTIMIZED: Relationships are loaded eagerly via entity configuration
            const users = await userRepository.find({
                take: limit
                // No relations needed - eager loading handles it automatically
            });

            res.json(users);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /users/:id - Get user by ID (OPTIMIZED: single query with relationships)
    router.get("/users/:id", async (req, res) => {
        try {
            const { id } = req.params;

            // OPTIMIZED: Single query loads user with all relationships
            const user = await userRepository.findOne({
                where: { id }
                // Relations loaded eagerly via entity configuration
            });

            if (!user) {
                return res.status(404).json({ error: "User not found" });
            }

            res.json(user);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /users/:id/posts - Get posts by user (OPTIMIZED: eager loading)
    router.get("/users/:id/posts", async (req, res) => {
        try {
            const { id } = req.params;
            const limit = parseInt(req.query.limit as string) || 10;

            // OPTIMIZED: Load posts with eager author relationship
            const posts = await postRepository.find({
                where: { authorId: id },
                take: limit
                // Author loaded eagerly via entity configuration
            });

            res.json(posts);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /posts - Get all posts (OPTIMIZED: eager loading relationships)
    router.get("/posts", async (req, res) => {
        try {
            const limit = parseInt(req.query.limit as string) || 10;

            // OPTIMIZED: Posts loaded with author and comments relationships
            const posts = await postRepository.find({
                take: limit
                // Author and comments loaded eagerly via entity configuration
            });

            res.json(posts);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /posts/:id - Get post by ID (OPTIMIZED: single query with all relationships)
    router.get("/posts/:id", async (req, res) => {
        try {
            const { id } = req.params;

            // OPTIMIZED: Single query loads post with author and all comments
            const post = await postRepository.findOne({
                where: { id }
                // Author and comments loaded eagerly via entity configuration
            });

            if (!post) {
                return res.status(404).json({ error: "Post not found" });
            }

            res.json(post);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /posts/:id/comments - Get comments by post (OPTIMIZED: eager loading)
    router.get("/posts/:id/comments", async (req, res) => {
        try {
            const { id } = req.params;
            const limit = parseInt(req.query.limit as string) || 50;

            // OPTIMIZED: Load comments with eager author relationship
            const comments = await commentRepository.find({
                where: { postId: id },
                take: limit
                // Author loaded eagerly via entity configuration
            });

            res.json(comments);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });

    return router;
}