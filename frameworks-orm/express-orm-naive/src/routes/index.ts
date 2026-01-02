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
    // GET /users - Get all users (NAIVE: lazy loading relationships)
    router.get("/users", async (req, res) => {
        try {
            const limit = parseInt(req.query.limit as string) || 10;

            // NAIVE: Load users without relationships - causes lazy loading!
            const users = await userRepository.find({
                take: limit
                // NO relations loaded - relationships accessed lazily
            });

            res.json(users);
        } catch (error: any) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /users/:id - Get user by ID
    router.get("/users/:id", async (req, res) => {
        try {
            const { id } = req.params;

            // NAIVE: Load user without relationships
            const user = await userRepository.findOne({
                where: { id }
                // NO relations loaded - causes lazy loading!
            });

            if (!user) {
                return res.status(404).json({ error: "User not found" });
            }

            res.json(user);
        } catch (error: any) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /users/:id/posts - Get posts by user
    router.get("/users/:id/posts", async (req, res) => {
        try {
            const { id } = req.params;
            const limit = parseInt(req.query.limit as string) || 10;

            // NAIVE: Query for posts - separate from user loading
            const posts = await postRepository.find({
                where: { author_id: id },
                take: limit
                // NO relations loaded - causes lazy loading!
            });

            res.json(posts);
        } catch (error: any) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /posts - Get all posts
    router.get("/posts", async (req, res) => {
        try {
            const limit = parseInt(req.query.limit as string) || 10;

            // NAIVE: Load posts without relationships
            const posts = await postRepository.find({
                take: limit
                // NO relations loaded - causes lazy loading!
            });

            res.json(posts);
        } catch (error: any) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /posts/:id - Get post by ID
    router.get("/posts/:id", async (req, res) => {
        try {
            const { id } = req.params;

            // NAIVE: Load post without relationships
            const post = await postRepository.findOne({
                where: { id }
                // NO relations loaded - causes lazy loading!
            });

            if (!post) {
                return res.status(404).json({ error: "Post not found" });
            }

            res.json(post);
        } catch (error: any) {
            res.status(500).json({ error: error.message });
        }
    });

    // GET /posts/:id/comments - Get comments by post
    router.get("/posts/:id/comments", async (req, res) => {
        try {
            const { id } = req.params;
            const limit = parseInt(req.query.limit as string) || 50;

            // NAIVE: Query for comments - separate from post loading
            const comments = await commentRepository.find({
                where: { post_id: id },
                take: limit
                // NO relations loaded - causes lazy loading!
            });

            res.json(comments);
        } catch (error: any) {
            res.status(500).json({ error: error.message });
        }
    });

    return router;
}