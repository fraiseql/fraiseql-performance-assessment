package graph

import (
	"context"
	"fmt"

	"github.com/benchmark/go-gqlgen/graph/model"
	"github.com/benchmark/go-gqlgen/internal/db"
)

type Resolver struct{}

// Query resolvers
func (r *queryResolver) Ping(ctx context.Context) (string, error) {
	return "pong", nil
}

func (r *queryResolver) User(ctx context.Context, id string) (*model.User, error) {
	loaders := GetLoaders(ctx)
	return loaders.UserLoader.Load(ctx, id)()
}

func (r *queryResolver) Users(ctx context.Context, limit *int) ([]*model.User, error) {
	lim := 10
	if limit != nil {
		lim = *limit
	}

	rows, err := db.Pool.Query(ctx, `
		SELECT id, username, first_name, last_name, bio
		FROM benchmark.tb_user
		ORDER BY created_at DESC
		LIMIT $1
	`, lim)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var users []*model.User
	for rows.Next() {
		var u model.User
		var firstName, lastName, bio *string
		if err := rows.Scan(&u.ID, &u.Username, &firstName, &lastName, &bio); err != nil {
			continue
		}
		u.FirstName = firstName
		u.LastName = lastName
		u.Bio = bio
		users = append(users, &u)
	}

	return users, nil
}

func (r *queryResolver) Post(ctx context.Context, id string) (*model.Post, error) {
	row := db.Pool.QueryRow(ctx, `
		SELECT id, fk_author, title, content
		FROM benchmark.tb_post
		WHERE id = $1
	`, id)

	var p model.Post
	var content *string
	if err := row.Scan(&p.ID, &p.AuthorID, &p.Title, &content); err != nil {
		return nil, nil
	}
	p.Content = content
	return &p, nil
}

func (r *queryResolver) Posts(ctx context.Context, limit *int) ([]*model.Post, error) {
	lim := 10
	if limit != nil {
		lim = *limit
	}

	rows, err := db.Pool.Query(ctx, `
		SELECT id, fk_author, title, content
		FROM benchmark.tb_post
		WHERE published = true
		ORDER BY created_at DESC
		LIMIT $1
	`, lim)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var posts []*model.Post
	for rows.Next() {
		var p model.Post
		var content *string
		if err := rows.Scan(&p.ID, &p.AuthorID, &p.Title, &content); err != nil {
			continue
		}
		p.Content = content
		posts = append(posts, &p)
	}

	return posts, nil
}

func (r *queryResolver) Comment(ctx context.Context, id string) (*model.Comment, error) {
	row := db.Pool.QueryRow(ctx, `
		SELECT id, fk_post, fk_author, content
		FROM benchmark.tb_comment
		WHERE id = $1
	`, id)

	var c model.Comment
	if err := row.Scan(&c.ID, &c.PostID, &c.AuthorID, &c.Content); err != nil {
		return nil, nil
	}
	return &c, nil
}

func (r *queryResolver) Comments(ctx context.Context, limit *int) ([]*model.Comment, error) {
	lim := 10
	if limit != nil {
		lim = *limit
	}

	rows, err := db.Pool.Query(ctx, `
		SELECT id, fk_post, fk_author, content
		FROM benchmark.tb_comment
		ORDER BY created_at DESC
		LIMIT $1
	`, lim)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var comments []*model.Comment
	for rows.Next() {
		var c model.Comment
		if err := rows.Scan(&c.ID, &c.PostID, &c.AuthorID, &c.Content); err != nil {
			continue
		}
		comments = append(comments, &c)
	}

	return comments, nil
}

// User field resolvers
func (r *userResolver) Posts(ctx context.Context, obj *model.User, limit *int) ([]*model.Post, error) {
	loaders := GetLoaders(ctx)
	posts, err := loaders.PostsByAuthorLoader.Load(ctx, obj.ID)()
	if err != nil {
		return nil, err
	}

	lim := 10
	if limit != nil {
		lim = *limit
	}
	if len(posts) > lim {
		posts = posts[:lim]
	}
	return posts, nil
}

func (r *userResolver) FollowerCount(ctx context.Context, obj *model.User) (int, error) {
	loaders := GetLoaders(ctx)
	return loaders.FollowerCountLoader.Load(ctx, obj.ID)()
}

// Post field resolvers
func (r *postResolver) Author(ctx context.Context, obj *model.Post) (*model.User, error) {
	loaders := GetLoaders(ctx)
	return loaders.UserLoader.Load(ctx, obj.AuthorID)()
}

func (r *postResolver) Comments(ctx context.Context, obj *model.Post, limit *int) ([]*model.Comment, error) {
	loaders := GetLoaders(ctx)
	comments, err := loaders.CommentsByPostLoader.Load(ctx, obj.ID)()
	if err != nil {
		return nil, err
	}

	lim := 10
	if limit != nil {
		lim = *limit
	}
	if len(comments) > lim {
		comments = comments[:lim]
	}
	return comments, nil
}

// Comment field resolvers
func (r *commentResolver) Author(ctx context.Context, obj *model.Comment) (*model.User, error) {
	loaders := GetLoaders(ctx)
	return loaders.UserLoader.Load(ctx, obj.AuthorID)()
}

func (r *commentResolver) Post(ctx context.Context, obj *model.Comment) (*model.Post, error) {
	row := db.Pool.QueryRow(ctx, `
		SELECT id, fk_author, title, content
		FROM benchmark.tb_post
		WHERE id = $1
	`, obj.PostID)

	var p model.Post
	var content *string
	if err := row.Scan(&p.ID, &p.AuthorID, &p.Title, &content); err != nil {
		return nil, nil
	}
	p.Content = content
	return &p, nil
}

// Mutation resolvers
func (r *mutationResolver) UpdateUser(ctx context.Context, id string, firstName *string, lastName *string, bio *string) (*model.User, error) {
	// Build dynamic update query
	query := "UPDATE benchmark.tb_user SET updated_at = NOW()"
	args := []interface{}{}
	argIdx := 1

	if firstName != nil {
		query += fmt.Sprintf(", first_name = $%d", argIdx)
		args = append(args, *firstName)
		argIdx++
	}
	if lastName != nil {
		query += fmt.Sprintf(", last_name = $%d", argIdx)
		args = append(args, *lastName)
		argIdx++
	}
	if bio != nil {
		query += fmt.Sprintf(", bio = $%d", argIdx)
		args = append(args, *bio)
		argIdx++
	}

	query += fmt.Sprintf(" WHERE id::text = $%d", argIdx)
	args = append(args, id)

	_, err := db.Pool.Exec(ctx, query, args...)
	if err != nil {
		return nil, err
	}

	// Return updated user via dataloader
	loaders := GetLoaders(ctx)
	loaders.UserLoader.Clear(ctx, id) // Clear cache
	return loaders.UserLoader.Load(ctx, id)()
}

type queryResolver struct{ *Resolver }
type mutationResolver struct{ *Resolver }
type userResolver struct{ *Resolver }
type postResolver struct{ *Resolver }
type commentResolver struct{ *Resolver }
