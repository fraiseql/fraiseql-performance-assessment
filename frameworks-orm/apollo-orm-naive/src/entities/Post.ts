import { Entity, PrimaryColumn, Column, OneToMany, ManyToOne } from "typeorm";
import { User } from "./User";
import { Comment } from "./Comment";

@Entity("tb_post")
export class Post {
    @PrimaryColumn()
    id!: string;

    @Column()
    title!: string;

    @Column({ nullable: true })
    content?: string;

    @Column()
    author_id!: string;

    // NAIVE: Set eager to false to demonstrate N+1 problems
    @ManyToOne(() => User, user => user.posts, {
        eager: false  // This causes lazy loading!
    })
    author!: User;

    @OneToMany(() => Comment, comment => comment.post, {
        eager: false  // This causes lazy loading!
    })
    comments!: Comment[];
}