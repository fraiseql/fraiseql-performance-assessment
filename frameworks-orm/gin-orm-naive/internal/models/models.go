package models

import "gorm.io/gorm"

// User model - NAIVE: No eager loading, uses lazy loading
type User struct {
	ID        string  `json:"id" gorm:"primaryKey"`
	Username  string  `json:"username" gorm:"uniqueIndex"`
	FirstName *string `json:"firstName,omitempty"`
	LastName  *string `json:"lastName,omitempty"`
	Bio       *string `json:"bio,omitempty"`

	// NAIVE: Relationships without Preload - causes lazy loading!
	Posts    []Post    `json:"posts,omitempty" gorm:"foreignKey:AuthorID"`
	Comments []Comment `json:"comments,omitempty" gorm:"foreignKey:AuthorID"`
}

// Post model - NAIVE: No eager loading, uses lazy loading
type Post struct {
	ID       string  `json:"id" gorm:"primaryKey"`
	Title    string  `json:"title"`
	Content  *string `json:"content,omitempty"`
	AuthorID string  `json:"authorId"`

	// NAIVE: Relationships without Preload - causes lazy loading!
	Author   User      `json:"author,omitempty" gorm:"foreignKey:AuthorID"`
	Comments []Comment `json:"comments,omitempty" gorm:"foreignKey:PostID"`
}

// Comment model - NAIVE: No eager loading, uses lazy loading
type Comment struct {
	ID       string `json:"id" gorm:"primaryKey"`
	Content  string `json:"content"`
	PostID   string `json:"postId"`
	AuthorID string `json:"authorId"`

	// NAIVE: Relationships without Preload - causes lazy loading!
	Post   Post `json:"post,omitempty" gorm:"foreignKey:PostID"`
	Author User `json:"author,omitempty" gorm:"foreignKey:AuthorID"`
}

// Set table names for trinity pattern
func (User) TableName() string {
	return "benchmark.tb_user"
}

func (Post) TableName() string {
	return "benchmark.tb_post"
}

func (Comment) TableName() string {
	return "benchmark.tb_comment"
}

// Database connection
var DB *gorm.DB

func SetDB(db *gorm.DB) {
	DB = db
}
