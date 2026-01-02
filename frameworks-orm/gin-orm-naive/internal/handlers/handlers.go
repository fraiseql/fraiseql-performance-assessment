package handlers

import (
	"net/http"
	"strconv"

	"gin-orm-naive/internal/models"
	"github.com/gin-gonic/gin"
)

// GetUsers - NAIVE: Load users without relationships - causes lazy loading!
func GetUsers(c *gin.Context) {
	limitStr := c.DefaultQuery("limit", "10")
	limit, err := strconv.Atoi(limitStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid limit"})
		return
	}

	var users []*models.User
	// NAIVE: Load users without relationships - causes lazy loading!
	if err := models.DB.Limit(limit).Find(&users).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, users)
}

// GetUser - NAIVE: Load user without relationships - causes lazy loading!
func GetUser(c *gin.Context) {
	id := c.Param("id")

	var user models.User
	// NAIVE: Load user without relationships - causes lazy loading!
	if err := models.DB.Where("id = ?", id).First(&user).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	c.JSON(http.StatusOK, &user)
}

// GetUserPosts - NAIVE: Query for posts - separate from user loading
func GetUserPosts(c *gin.Context) {
	userID := c.Param("id")
	limitStr := c.DefaultQuery("limit", "10")
	limit, err := strconv.Atoi(limitStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid limit"})
		return
	}

	var posts []*models.Post
	// NAIVE: Query for posts - separate from user loading
	if err := models.DB.Where("author_id = ?", userID).Limit(limit).Find(&posts).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, posts)
}

// GetPosts - NAIVE: Load posts without relationships - causes lazy loading!
func GetPosts(c *gin.Context) {
	limitStr := c.DefaultQuery("limit", "10")
	limit, err := strconv.Atoi(limitStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid limit"})
		return
	}

	var posts []*models.Post
	// NAIVE: Load posts without relationships - causes lazy loading!
	if err := models.DB.Limit(limit).Find(&posts).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, posts)
}

// GetPost - NAIVE: Load post without relationships - causes lazy loading!
func GetPost(c *gin.Context) {
	id := c.Param("id")

	var post models.Post
	// NAIVE: Load post without relationships - causes lazy loading!
	if err := models.DB.Where("id = ?", id).First(&post).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Post not found"})
		return
	}

	c.JSON(http.StatusOK, &post)
}

// GetPostComments - NAIVE: Query for comments - separate from post loading
func GetPostComments(c *gin.Context) {
	postID := c.Param("id")
	limitStr := c.DefaultQuery("limit", "50")
	limit, err := strconv.Atoi(limitStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid limit"})
		return
	}

	var comments []*models.Comment
	// NAIVE: Query for comments - separate from post loading
	if err := models.DB.Where("post_id = ?", postID).Limit(limit).Find(&comments).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, comments)
}

// Health check
func Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "healthy"})
}
