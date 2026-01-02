import { Entity, PrimaryColumn, Column, ManyToOne } from "typeorm";

@Entity("tb_comments")
export class Comment {
    @PrimaryColumn()
    id: string;

    @Column({ type: "text" })
    content: string;

    @Column({ name: "post_id" })
    postId: string;

    @Column({ name: "author_id" })
    authorId: string;

    // OPTIMIZED: Use eager loading to prevent N+1 queries in GraphQL
    @ManyToOne(() => Post, post => post.comments, {
        eager: true  // Preload post relationship
    })
    post: Post;

    @ManyToOne(() => User, user => user.comments, {
        eager: true  // Preload author relationship
    })
    author: User;
}