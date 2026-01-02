package main

import (
	"log"
	"os"

	"gin-orm-naive/internal/db"
	"gin-orm-naive/internal/handlers"
	"github.com/gin-gonic/gin"
)

func main() {
	// Initialize database
	_, err := db.InitDB()
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}

	// Create Gin router
	r := gin.Default()

	// Routes
	r.GET("/health", handlers.Health)
	r.GET("/api/users", handlers.GetUsers)
	r.GET("/api/users/:id/posts", handlers.GetUserPosts)
	r.GET("/api/users/:id", handlers.GetUser)
	r.GET("/api/posts/:id/comments", handlers.GetPostComments)
	r.GET("/api/posts/:id", handlers.GetPost)
	r.GET("/api/posts", handlers.GetPosts)

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("🚀 Naive Gin ORM server ready at http://localhost:%s", port)
	log.Printf("📊 Query logging enabled - watch for N+1 patterns!")
	log.Printf("📍 API endpoints available at /api/*")

	if err := r.Run(":" + port); err != nil {
		log.Fatal("Failed to start server:", err)
	}
}
