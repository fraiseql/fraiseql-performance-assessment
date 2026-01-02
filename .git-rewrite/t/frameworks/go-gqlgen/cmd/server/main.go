package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/benchmark/go-gqlgen/internal/db"
)

func main() {
	// Initialize database pool
	if err := db.Init(); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer db.Close()

	// Serve GraphQL endpoint
	http.HandleFunc("/graphql", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		var query struct {
			Query string                 `json:"query"`
			Vars  map[string]interface{} `json:"variables"`
		}

		if err := json.NewDecoder(r.Body).Decode(&query); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		// Create dataloaders (for future use with full GraphQL parser)
		// loaders := graph.NewLoaders()
		// ctx := graph.WithLoaders(r.Context(), loaders)

		// For now, handle simple ping query
		if query.Query == "{ ping }" {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(map[string]interface{}{
				"data": map[string]interface{}{
					"ping": "pong",
				},
			})
			return
		}

		// Return a basic response for other queries (GraphQL would need full parser)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]interface{}{
			"data":   nil,
			"errors": []string{"GraphQL queries not fully implemented yet"},
		})
	})

	// Health check
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		if err := db.Pool.Ping(r.Context()); err != nil {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte(`{"status":"unhealthy"}`))
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"healthy","framework":"go-gqlgen"}`))
	})

	// Prometheus metrics
	http.Handle("/metrics", promhttp.Handler())

	// Playground (GraphQL IDE)
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		html := `<!DOCTYPE html>
		<html>
		<head>
			<title>GraphQL Playground</title>
			<style>
				body { font-family: monospace; padding: 20px; }
				#editor { width: 100%; height: 300px; font-family: monospace; border: 1px solid #ccc; }
				button { padding: 10px 20px; margin: 10px 0; }
			</style>
		</head>
		<body>
			<h1>GraphQL API</h1>
			<textarea id="editor">{ ping }</textarea><br>
			<button onclick="sendQuery()">Run Query</button>
			<pre id="result"></pre>
			<script>
				function sendQuery() {
					fetch('/graphql', {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({ query: document.getElementById('editor').value })
					}).then(r => r.json()).then(d => {
						document.getElementById('result').textContent = JSON.stringify(d, null, 2);
					});
				}
			</script>
		</body>
		</html>`
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(html))
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "4003"
	}

	log.Printf("🚀 gqlgen server ready at http://localhost:%s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
