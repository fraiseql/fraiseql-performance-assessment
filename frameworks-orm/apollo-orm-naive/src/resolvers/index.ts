import { ObjectType, Field, ID, Resolver, Query, FieldResolver, Arg, Root } from "type-graphql";
import { Repository } from "typeorm";
import { User } from "../entities/User";
import { Post } from "../entities/Post";
import { Comment } from "../entities/Comment";

// GraphQL Types
@ObjectType()
export class UserType {
    @Field(() => ID)
    id!: string;

    @Field()
    username!: string;

    @Field({ nullable: true })
    firstName?: string;

    @Field({ nullable: true })
    lastName?: string;

    @Field({ nullable: true })
    bio?: string;

    // NAIVE: These field resolvers cause N+1 queries
    @Field(() => [PostType])
    posts!: PostType[];

    @Field(() => [CommentType])
    comments!: CommentType[];
}

@ObjectType()
export class PostType {
    @Field(() => ID)
    id!: string;

    @Field()
    title!: string;

    @Field({ nullable: true })
    content?: string;

    @Field()
    author_id!: string;

    // NAIVE: These field resolvers cause N+1 queries
    @Field(() => UserType)
    author!: UserType;

    @Field(() => [CommentType])
    comments!: CommentType[];
}

@ObjectType()
export class CommentType {
    @Field(() => ID)
    id!: string;

    @Field()
    content!: string;

    @Field()
    post_id!: string;

    @Field()
    author_id!: string;

    // NAIVE: These field resolvers cause N+1 queries
    @Field(() => PostType)
    post!: PostType;

    @Field(() => UserType)
    author!: UserType;
}

// Resolvers with N+1 problems
@Resolver(() => UserType)
export class UserResolver {
    constructor(
        private userRepository: Repository<User>,
        private postRepository: Repository<Post>,
        private commentRepository: Repository<Comment>
    ) {}

    @Query(() => UserType, { nullable: true })
    async user(@Arg("id") id: string) {
        // Get user without loading relationships (no eager loading)
        return await this.userRepository.findOne({
            where: { id }
            // NO relations loaded - causes lazy loading
        });
    }

    @Query(() => [UserType])
    async users(@Arg("limit", { defaultValue: 10 }) limit: number) {
        // Get users without loading relationships
        return await this.userRepository.find({
            take: limit
            // NO relations loaded - causes lazy loading
        });
    }

    // NAIVE: Called once per user in result set (N+1 problem!)
    @FieldResolver(() => [PostType])
    async posts(@Root() user: UserType) {
        // This resolver is called for EACH user (N+1 problem!)
        return await this.postRepository.find({
            where: { author_id: user.id }
        });
    }

    // NAIVE: Called once per user in result set (N+1 problem!)
    @FieldResolver(() => [CommentType])
    async comments(@Root() user: UserType) {
        // This resolver is called for EACH user (N+1 problem!)
        return await this.commentRepository.find({
            where: { author_id: user.id }
        });
    }
}

@Resolver(() => PostType)
export class PostResolver {
    constructor(
        private postRepository: Repository<Post>,
        private userRepository: Repository<User>,
        private commentRepository: Repository<Comment>
    ) {}

    @Query(() => PostType, { nullable: true })
    async post(@Arg("id") id: string) {
        // Get post without loading relationships
        return await this.postRepository.findOne({
            where: { id }
            // NO relations loaded - causes lazy loading
        });
    }

    @Query(() => [PostType])
    async posts(@Arg("limit", { defaultValue: 10 }) limit: number) {
        // Get posts without loading relationships
        return await this.postRepository.find({
            take: limit
            // NO relations loaded - causes lazy loading
        });
    }

    // NAIVE: Called once per post (N+1 problem!)
    @FieldResolver(() => UserType)
    async author(@Root() post: PostType) {
        // This resolver is called for EACH post (N+1 problem!)
        return await this.userRepository.findOne({
            where: { id: post.author_id }
        });
    }

    // NAIVE: Called once per post (N+1 problem!)
    @FieldResolver(() => [CommentType])
    async comments(@Root() post: PostType) {
        // This resolver is called for EACH post (N+1 problem!)
        return await this.commentRepository.find({
            where: { post_id: post.id }
        });
    }
}