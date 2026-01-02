package model

type User struct {
	ID        string  `json:"id"`
	Username  string  `json:"username"`
	FirstName *string `json:"firstName"`
	LastName  *string `json:"lastName"`
	Bio       *string `json:"bio"`
}

type Post struct {
	ID       string `json:"id"`
	Title    string `json:"title"`
	Content  *string `json:"content"`
	AuthorID string `json:"authorId"`
}

type Comment struct {
	ID       string `json:"id"`
	Content  string `json:"content"`
	AuthorID string `json:"authorId"`
	PostID   string `json:"postId"`
}
