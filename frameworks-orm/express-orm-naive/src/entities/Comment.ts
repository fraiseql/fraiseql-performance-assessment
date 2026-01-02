import { Entity, PrimaryColumn, Column, ManyToOne } from "typeorm";
import { Post } from "./Post";
import { User } from "./User";

@Entity("tb_comment")
export class Comment {
    @PrimaryColumn()
    id!: string;

    @Column()
    content!: string;

    @Column()
    post_id!: string;

    @Column()
    author_id!: string;

    // NAIVE: Set eager to false to demonstrate N+1 problems
    @ManyToOne(() => Post, post => post.comments, {
        eager: false  // This causes lazy loading!
    })
    post!: Post;

    @ManyToOne(() => User, user => user.comments, {
        eager: false  // This causes lazy loading!
    })
    author!: User;
}