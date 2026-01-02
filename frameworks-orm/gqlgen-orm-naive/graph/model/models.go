package model

import "gorm.io/gorm"

var DB *gorm.DB

func SetDB(db *gorm.DB) {
	DB = db
}

// GORM models with explicit table names and column mapping
type User struct {
	ID        string  `gorm:"column:id;primaryKey"`
	Username  string  `gorm:"column:username"`
	FirstName *string `gorm:"column:first_name"`
	LastName  *string `gorm:"column:last_name"`
	Bio       *string `gorm:"column:bio"`
}

func (User) TableName() string {
	return "benchmark.users"
}

type Post struct {
	ID       string  `gorm:"column:id;primaryKey"`
	Title    string  `gorm:"column:title"`
	Content  *string `gorm:"column:content"`
	AuthorID string  `gorm:"column:author_id"`
}

func (Post) TableName() string {
	return "benchmark.posts"
}

type Comment struct {
	ID       string `gorm:"column:id;primaryKey"`
	Content  string `gorm:"column:content"`
	PostID   string `gorm:"column:post_id"`
	AuthorID string `gorm:"column:author_id"`
}

func (Comment) TableName() string {
	return "benchmark.comments"
}
