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
         FROM benchmark.tb_user
         ORDER BY created_at DESC
         LIMIT $1`,
        [limit]
      );
    },

    post: async (_: any, { id }: { id: string }) => {
      return queryOne(
        `SELECT id, author_id, title, content, published as status
         FROM benchmark.tb_post
         WHERE id = $1`,
        [id]
      );
    },

    posts: async (_: any, { limit }: { limit: number }) => {
      return query(
        `SELECT id, author_id, title, content, published as status
         FROM benchmark.tb_post
         WHERE published = true
         ORDER BY created_at DESC
         LIMIT $1`,
        [limit]
      );
    },

    comment: async (_: any, { id }: { id: string }) => {
      return queryOne(
        `SELECT id, fk_post as post_id, fk_author as author_id, content
         FROM benchmark.tb_comment
         WHERE id = $1`,
        [id]
      );
    },

    comments: async (_: any, { limit }: { limit: number }) => {
      return query(
        `SELECT id, fk_post as post_id, fk_author as author_id, content
         FROM benchmark.tb_comment
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
      return posts.slice(0, limit || 10);
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
      return comments.slice(0, limit || 10);
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
          `UPDATE benchmark.tb_user
           SET ${updates.join(', ')}, updated_at = NOW()
           WHERE id = $${paramIndex}`,
          values
        );
      }

      return queryOne(
        `SELECT id, username, first_name, last_name, bio
         FROM benchmark.tb_user WHERE id = $1`,
        [id]
      );
    },
  },
};
