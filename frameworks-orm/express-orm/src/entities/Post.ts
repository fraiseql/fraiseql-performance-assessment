import { Entity, PrimaryColumn, Column, OneToMany, ManyToOne } from "typeorm";

@Entity("tb_posts")
export class Post {
    @PrimaryColumn()
    id: string;

    @Column()
    title: string;

    @Column({ type: "text" })
    content: string;

    @Column({ name: "author_id" })
    authorId: string;

    // OPTIMIZED: Use eager loading to prevent N+1 queries
    @ManyToOne(() => User, user => user.posts, {
        eager: true  // Preload author relationship
    })
    author: User;

    // OPTIMIZED: Use eager loading for comments
    @OneToMany(() => Comment, comment => comment.post, {
        eager: true  // Preload comments relationship
    })
    comments: Comment[];
}