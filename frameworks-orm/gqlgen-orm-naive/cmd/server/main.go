package main

import (
	"log"
	"net/http"
	"os"

	"github.com/99designs/gqlgen/graphql/handler"
	"github.com/99designs/gqlgen/graphql/playground"
	"github.com/go-chi/chi/v5"

	"gqlgen-orm-naive/graph"
	"gqlgen-orm-naive/graph/resolver"
	"gqlgen-orm-naive/internal/db"
)

func main() {
	// Initialize database
	_, err := db.InitDB()
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}

	// Create GraphQL handler
	srv := handler.NewDefaultServer(graph.NewExecutableSchema(graph.Config{Resolvers: &resolver.Resolver{}}))

	// Setup router
	r := chi.NewRouter()

	// Health check
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("healthy"))
	})

	// GraphQL playground
	r.Get("/", playground.Handler("GraphQL playground", "/query"))

	// GraphQL endpoint
	r.Handle("/query", srv)

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("🚀 Naive gqlgen server ready at http://localhost:%s", port)
	log.Printf("📊 Query logging enabled - watch for N+1 patterns!")
	log.Printf("🎮 GraphQL playground: http://localhost:%s", port)

	log.Fatal(http.ListenAndServe(":"+port, r))
}
