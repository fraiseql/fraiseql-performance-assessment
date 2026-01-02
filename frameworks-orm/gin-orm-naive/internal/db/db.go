package db

import (
	"fmt"
	"os"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"gin-orm-naive/internal/models"
)

func InitDB() (*gorm.DB, error) {
	host := getEnv("DB_HOST", "postgres")
	port := getEnv("DB_PORT", "5432")
	user := getEnv("DB_USER", "benchmark")
	password := getEnv("DB_PASSWORD", "benchmark123")
	dbname := getEnv("DB_NAME", "fraiseql_benchmark")

	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info), // Log all queries to show N+1!
	})
	if err != nil {
		return nil, err
	}

	// Set the global DB instance
	models.SetDB(db)

	return db, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
