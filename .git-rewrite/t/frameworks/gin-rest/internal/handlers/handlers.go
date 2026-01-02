package handlers

import (
	"context"
	"net/http"
	"strconv"
	"strings"

	"github.com/benchmark/gin-rest/internal/db"
	"github.com/gin-gonic/gin"
)

func GetUsers(c *gin.Context) {
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))

	rows, err := db.Pool.Query(c.Request.Context(), `
		SELECT id, username, first_name, last_name, bio
		FROM benchmark.tb_user
		ORDER BY created_at DESC
		LIMIT $1
	`, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var users []map[string]interface{}
	for rows.Next() {
		var id, username string
		var firstName, lastName, bio *string
		rows.Scan(&id, &username, &firstName, &lastName, &bio)
		users = append(users, map[string]interface{}{
			"id": id, "username": username,
			"first_name": firstName, "last_name": lastName, "bio": bio,
		})
	}

	c.JSON(http.StatusOK, users)
}

func GetUser(c *gin.Context) {
	id := c.Param("id")
	include := strings.Split(c.Query("include"), ",")

	ctx := c.Request.Context()

	row := db.Pool.QueryRow(ctx, `
		SELECT id, username, first_name, last_name, bio
		FROM benchmark.tb_user WHERE id = $1
	`, id)

	var user struct {
		ID        string  `json:"id"`
		Username  string  `json:"username"`
		FirstName *string `json:"first_name"`
		LastName  *string `json:"last_name"`
		Bio       *string `json:"bio"`
	}
	if err := row.Scan(&user.ID, &user.Username, &user.FirstName, &user.LastName, &user.Bio); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	result := gin.H{
		"id": user.ID, "username": user.Username,
		"first_name": user.FirstName, "last_name": user.LastName, "bio": user.Bio,
	}

	for _, inc := range include {
		switch inc {
		case "posts":
			result["posts"] = getPostsByAuthor(ctx, id)
		}
	}

	c.JSON(http.StatusOK, result)
}

func UpdateUser(c *gin.Context) {
	id := c.Param("id")

	var body struct {
		FirstName *string `json:"first_name"`
		LastName  *string `json:"last_name"`
		Bio       *string `json:"bio"`
	}

	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	query := "UPDATE benchmark.tb_user SET updated_at = NOW()"
	args := []interface{}{}
	argIdx := 1

	if body.FirstName != nil {
		query += ", first_name = $" + strconv.Itoa(argIdx)
		args = append(args, *body.FirstName)
		argIdx++
	}
	if body.LastName != nil {
		query += ", last_name = $" + strconv.Itoa(argIdx)
		args = append(args, *body.LastName)
		argIdx++
	}
	if body.Bio != nil {
		query += ", bio = $" + strconv.Itoa(argIdx)
		args = append(args, *body.Bio)
		argIdx++
	}

	query += " WHERE id = $" + strconv.Itoa(argIdx)
	args = append(args, id)

	_, err := db.Pool.Exec(c.Request.Context(), query, args...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "updated"})
}

func GetPosts(c *gin.Context) {
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))

	rows, err := db.Pool.Query(c.Request.Context(), `
		SELECT id, fk_author, title, content
		FROM benchmark.tb_post
		WHERE published = true
		ORDER BY created_at DESC
		LIMIT $1
	`, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var posts []map[string]interface{}
	for rows.Next() {
		var id, authorID, title string
		var content *string
		rows.Scan(&id, &authorID, &title, &content)
		posts = append(posts, map[string]interface{}{
			"id": id, "author_id": authorID, "title": title, "content": content,
		})
	}

	c.JSON(http.StatusOK, posts)
}

func GetPost(c *gin.Context) {
	id := c.Param("id")

	row := db.Pool.QueryRow(c.Request.Context(), `
		SELECT id, fk_author, title, content
		FROM benchmark.tb_post
		WHERE id = $1
	`, id)

	var post struct {
		ID       string  `json:"id"`
		AuthorID string  `json:"author_id"`
		Title    string  `json:"title"`
		Content  *string `json:"content"`
	}
	if err := row.Scan(&post.ID, &post.AuthorID, &post.Title, &post.Content); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Post not found"})
		return
	}

	c.JSON(http.StatusOK, post)
}

func getPostsByAuthor(ctx context.Context, authorID string) []map[string]interface{} {
	rows, err := db.Pool.Query(ctx, `
		SELECT id, title, content FROM benchmark.tb_post
		WHERE fk_author = $1 AND published = true
		ORDER BY created_at DESC LIMIT 10
	`, authorID)
	if err != nil {
		return []map[string]interface{}{}
	}
	defer rows.Close()

	var posts []map[string]interface{}
	for rows.Next() {
		var id, title string
		var content *string
		rows.Scan(&id, &title, &content)
		posts = append(posts, map[string]interface{}{"id": id, "title": title, "content": content})
	}
	return posts
}
