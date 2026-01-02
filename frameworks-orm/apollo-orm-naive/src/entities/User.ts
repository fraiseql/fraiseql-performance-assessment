import { Entity, PrimaryColumn, Column, OneToMany } from "typeorm";
import { Post } from "./Post";
import { Comment } from "./Comment";

@Entity("tb_user")
export class User {
    @PrimaryColumn()
    id!: string;

    @Column()
    username!: string;

    @Column({ nullable: true })
    first_name?: string;

    @Column({ nullable: true })
    last_name?: string;

    @Column({ nullable: true })
    bio?: string;

    // NAIVE: Set eager to false to demonstrate N+1 problems
    @OneToMany(() => Post, post => post.author, {
        eager: false  // This causes lazy loading!
    })
    posts!: Post[];

    @OneToMany(() => Comment, comment => comment.author, {
        eager: false  // This causes lazy loading!
    })
    comments!: Comment[];
}