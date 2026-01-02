package graph

import (
	"context"
	"time"

	"github.com/benchmark/go-gqlgen/graph/model"
	"github.com/benchmark/go-gqlgen/internal/db"
	"github.com/graph-gophers/dataloader/v7"
)

type Loaders struct {
	UserLoader              *dataloader.Loader[string, *model.User]
	PostsByAuthorLoader     *dataloader.Loader[string, []*model.Post]
	CommentsByPostLoader    *dataloader.Loader[string, []*model.Comment]
	FollowerCountLoader     *dataloader.Loader[string, int]
}

func NewLoaders() *Loaders {
	return &Loaders{
		UserLoader: dataloader.NewBatchedLoader(
			batchUsers,
			dataloader.WithWait[string, *model.User](2*time.Millisecond),
			dataloader.WithBatchCapacity[string, *model.User](100),
		),
		PostsByAuthorLoader: dataloader.NewBatchedLoader(
			batchPostsByAuthor,
			dataloader.WithWait[string, []*model.Post](2*time.Millisecond),
			dataloader.WithBatchCapacity[string, []*model.Post](100),
		),
		CommentsByPostLoader: dataloader.NewBatchedLoader(
			batchCommentsByPost,
			dataloader.WithWait[string, []*model.Comment](2*time.Millisecond),
			dataloader.WithBatchCapacity[string, []*model.Comment](100),
		),
		FollowerCountLoader: dataloader.NewBatchedLoader(
			batchFollowerCounts,
			dataloader.WithWait[string, int](2*time.Millisecond),
			dataloader.WithBatchCapacity[string, int](100),
		),
	}
}

func batchUsers(ctx context.Context, keys []string) []*dataloader.Result[*model.User] {
	results := make([]*dataloader.Result[*model.User], len(keys))

	rows, err := db.Pool.Query(ctx, `
		SELECT id, username, first_name, last_name, bio
		FROM benchmark.tb_user
		WHERE id::text = ANY($1)
	`, keys)
	if err != nil {
		for i := range results {
			results[i] = &dataloader.Result[*model.User]{Error: err}
		}
		return results
	}
	defer rows.Close()

	userMap := make(map[string]*model.User)
	for rows.Next() {
		var u model.User
		var firstName, lastName, bio *string
		if err := rows.Scan(&u.ID, &u.Username, &firstName, &lastName, &bio); err != nil {
			continue
		}
		u.FirstName = firstName
		u.LastName = lastName
		u.Bio = bio
		userMap[u.ID] = &u
	}

	for i, key := range keys {
		if user, ok := userMap[key]; ok {
			results[i] = &dataloader.Result[*model.User]{Data: user}
		} else {
			results[i] = &dataloader.Result[*model.User]{Data: nil}
		}
	}

	return results
}

func batchPostsByAuthor(ctx context.Context, authorIDs []string) []*dataloader.Result[[]*model.Post] {
	results := make([]*dataloader.Result[[]*model.Post], len(authorIDs))

	rows, err := db.Pool.Query(ctx, `
		SELECT id, fk_author, title, content
		FROM benchmark.tb_post
		WHERE fk_author::text = ANY($1) AND published = true
		ORDER BY created_at DESC
	`, authorIDs)
	if err != nil {
		for i := range results {
			results[i] = &dataloader.Result[[]*model.Post]{Error: err}
		}
		return results
	}
	defer rows.Close()

	postMap := make(map[string][]*model.Post)
	for rows.Next() {
		var p model.Post
		var authorID string
		var content *string
		if err := rows.Scan(&p.ID, &authorID, &p.Title, &content); err != nil {
			continue
		}
		p.AuthorID = authorID
		p.Content = content
		postMap[authorID] = append(postMap[authorID], &p)
	}

	for i, authorID := range authorIDs {
		posts := postMap[authorID]
		if posts == nil {
			posts = []*model.Post{}
		}
		results[i] = &dataloader.Result[[]*model.Post]{Data: posts}
	}

	return results
}

func batchCommentsByPost(ctx context.Context, postIDs []string) []*dataloader.Result[[]*model.Comment] {
	results := make([]*dataloader.Result[[]*model.Comment], len(postIDs))

	rows, err := db.Pool.Query(ctx, `
		SELECT id, fk_post, fk_author, content
		FROM benchmark.tb_comment
		WHERE fk_post::text = ANY($1)
		ORDER BY created_at DESC
	`, postIDs)
	if err != nil {
		for i := range results {
			results[i] = &dataloader.Result[[]*model.Comment]{Error: err}
		}
		return results
	}
	defer rows.Close()

	commentMap := make(map[string][]*model.Comment)
	for rows.Next() {
		var c model.Comment
		var postID, authorID string
		if err := rows.Scan(&c.ID, &postID, &authorID, &c.Content); err != nil {
			continue
		}
		c.PostID = postID
		c.AuthorID = authorID
		commentMap[postID] = append(commentMap[postID], &c)
	}

	for i, postID := range postIDs {
		comments := commentMap[postID]
		if comments == nil {
			comments = []*model.Comment{}
		}
		results[i] = &dataloader.Result[[]*model.Comment]{Data: comments}
	}

	return results
}

func batchFollowerCounts(ctx context.Context, userIDs []string) []*dataloader.Result[int] {
	results := make([]*dataloader.Result[int], len(userIDs))

	// For now, return 0 as we may not have a followers table
	for i := range results {
		results[i] = &dataloader.Result[int]{Data: 0}
	}

	return results
}

// Context key for dataloaders
type loadersKey struct{}

func WithLoaders(ctx context.Context, loaders *Loaders) context.Context {
	return context.WithValue(ctx, loadersKey{}, loaders)
}

func GetLoaders(ctx context.Context) *Loaders {
	return ctx.Value(loadersKey{}).(*Loaders)
}
