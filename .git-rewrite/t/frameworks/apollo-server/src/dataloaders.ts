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
         FROM benchmark.tb_user
         WHERE id = ANY($1)`,
        [ids]
      );
      const userMap = new Map(users.map(u => [u.id, u]));
      return ids.map(id => userMap.get(id) || null);
    }),

    // Batch load posts by author ID
    postsByAuthorLoader: new DataLoader<string, Post[]>(async (authorIds) => {
      const posts = await query<Post>(
        `SELECT id, author_id, title, content, published as status
         FROM benchmark.tb_post
         WHERE fk_author IN (SELECT pk_user FROM benchmark.tb_user WHERE id = ANY($1))
         ORDER BY created_at DESC
         LIMIT 100`,
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
        `SELECT c.id, c.fk_post as post_id, c.fk_author as author_id, c.content
         FROM benchmark.tb_comment c
         WHERE c.fk_post IN (SELECT pk_post FROM benchmark.tb_post WHERE id = ANY($1))
         ORDER BY c.created_at DESC
         LIMIT 100`,
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
        `SELECT u.id as following_id, COUNT(*)::text as count
         FROM benchmark.tb_user_follows uf
         JOIN benchmark.tb_user u ON uf.fk_following = u.pk_user
         WHERE u.id = ANY($1)
         GROUP BY u.id`,
        [userIds]
      );
      const countMap = new Map(counts.map(c => [c.following_id, parseInt(c.count)]));
      return userIds.map(id => countMap.get(id) || 0);
    }),
  };
}

export type DataLoaders = ReturnType<typeof createDataLoaders>;
