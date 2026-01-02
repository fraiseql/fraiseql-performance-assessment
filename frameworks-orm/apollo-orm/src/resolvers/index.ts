import { ObjectType, Field, ID, Resolver, Query, Arg } from "type-graphql";
import { Repository } from "typeorm";
import { User } from "../entities/User.js";
import { Post } from "../entities/Post.js";
import { Comment } from "../entities/Comment.js";

// GraphQL Types - OPTIMIZED: Relationships are preloaded
@ObjectType()
export class UserType {
    @Field(() => ID)
    id: string;

    @Field()
    username: string;

    @Field({ nullable: true })
    firstName: string;

    @Field({ nullable: true })
    lastName: string;

    @Field({ nullable: true })
    bio: string;

    // OPTIMIZED: No field resolvers - relationships preloaded by eager loading
    @Field(() => [PostType])
    posts: PostType[];

    @Field(() => [CommentType])
    comments: CommentType[];
}

@ObjectType()
export class PostType {
    @Field(() => ID)
    id: string;

    @Field()
    title: string;

    @Field({ nullable: true })
    content: string;

    @Field()
    authorId: string;

    // OPTIMIZED: No field resolvers - relationships preloaded by eager loading
    @Field(() => UserType)
    author: UserType;

    @Field(() => [CommentType])
    comments: CommentType[];
}

@ObjectType()
export class CommentType {
    @Field(() => ID)
    id: string;

    @Field()
    content: string;

    @Field()
    postId: string;

    @Field()
    authorId: string;

    // OPTIMIZED: No field resolvers - relationships preloaded by eager loading
    @Field(() => PostType)
    post: PostType;

    @Field(() => UserType)
    author: UserType;
}

// OPTIMIZED Resolvers - No N+1 query problems!
@Resolver(() => UserType)
export class UserResolver {
    constructor(
        private userRepository: Repository<User>,
        private postRepository: Repository<Post>,
        private commentRepository: Repository<Comment>
    ) {}

    @Query(() => UserType, { nullable: true })
    async user(@Arg("id") id: string) {
        // OPTIMIZED: Single query loads user with all relationships
        return await this.userRepository.findOne({
            where: { id }
            // Relationships loaded eagerly via entity configuration
        });
    }

    @Query(() => [UserType])
    async users(@Arg("limit", { defaultValue: 10 }) limit: number) {
        // OPTIMIZED: Single query loads users with all relationships
        return await this.userRepository.find({
            take: limit
            // Relationships loaded eagerly via entity configuration
        });
    }

    // OPTIMIZED: No field resolvers needed - relationships preloaded!
    // No @FieldResolver methods that cause N+1 queries
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
        // OPTIMIZED: Single query loads post with author and all comments
        return await this.postRepository.findOne({
            where: { id }
            // Author and comments loaded eagerly via entity configuration
        });
    }

    @Query(() => [PostType])
    async posts(@Arg("limit", { defaultValue: 10 }) limit: number) {
        // OPTIMIZED: Single query loads posts with authors and comments
        return await this.postRepository.find({
            take: limit
            // Author and comments loaded eagerly via entity configuration
        });
    }

    // OPTIMIZED: No field resolvers needed - relationships preloaded!
    // No @FieldResolver methods that cause N+1 queries
}