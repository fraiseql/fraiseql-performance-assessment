import { Entity, PrimaryColumn, Column, OneToMany, ManyToOne } from "typeorm";

@Entity("tb_users")
export class User {
    @PrimaryColumn()
    id: string;

    @Column()
    username: string;

    @Column({ nullable: true })
    first_name: string;

    @Column({ nullable: true })
    last_name: string;

    @Column({ nullable: true })
    bio: string;

    // OPTIMIZED: Use eager loading to prevent N+1 queries in GraphQL
    @OneToMany(() => Post, post => post.author, {
        eager: true  // Preload relationships automatically
    })
    posts: Post[];

    @OneToMany(() => Comment, comment => comment.author, {
        eager: true  // Preload relationships automatically
    })
    comments: Comment[];
}