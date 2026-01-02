.PHONY: help seed-small seed-medium seed-large seed-xlarge clean db-stats generate-datasets up down logs

# Default target
help:
	@echo "FraiseQL Performance Assessment - Makefile"
	@echo ""
	@echo "Data seeding targets:"
	@echo "  make seed-small       - Seed with small dataset (100 users, 500 posts)"
	@echo "  make seed-medium      - Seed with medium dataset (1K users, 5K posts)"
	@echo "  make seed-large       - Seed with large dataset (10K users, 100K posts)"
	@echo "  make seed-xlarge      - Seed with xlarge dataset (50K users, 500K posts)"
	@echo ""
	@echo "Database targets:"
	@echo "  make db-stats         - Show database table statistics"
	@echo "  make clean-db         - Drop and recreate database"
	@echo ""
	@echo "Dataset targets:"
	@echo "  make generate-datasets- Generate JMeter parameterized datasets"
	@echo ""
	@echo "Container targets:"
	@echo "  make up               - Start all containers"
	@echo "  make down             - Stop all containers"
	@echo "  make logs             - Show docker-compose logs"
	@echo ""

# ============================================================================
# Data Seeding Targets
# ============================================================================

seed-small:
	@echo "Seeding small dataset (100 users, 500 posts, 2K comments)..."
	@docker-compose down -v
	@DATA_VOLUME=small docker-compose up -d postgres
	@echo "Waiting for database to be ready..."
	@sleep 10
	@echo "✓ Small dataset seeded"
	@make db-stats

seed-medium:
	@echo "Seeding medium dataset (1K users, 5K posts, 20K comments)..."
	@docker-compose down -v
	@DATA_VOLUME=medium docker-compose up -d postgres
	@echo "Waiting for database to be ready..."
	@sleep 15
	@echo "Loading medium dataset..."
	@docker-compose exec -T postgres psql -U benchmark -d fraiseql_benchmark \
		-f /scripts/05-large-dataset.sql 2>&1 | grep -E "Generating|Syncing|complete" || true
	@echo "✓ Medium dataset seeded"
	@make db-stats

seed-large:
	@echo "Seeding large dataset (10K users, 100K posts, 500K comments)..."
	@docker-compose down -v
	@DATA_VOLUME=large docker-compose up -d postgres
	@echo "Waiting for database to be ready..."
	@sleep 20
	@echo "Loading large dataset..."
	@docker-compose exec -T postgres psql -U benchmark -d fraiseql_benchmark \
		-f /scripts/05-large-dataset.sql 2>&1 | grep -E "Generating|Syncing|complete" || true
	@echo "✓ Large dataset seeded"
	@make db-stats

seed-xlarge:
	@echo "Seeding xlarge dataset (50K users, 500K posts, 2M comments)..."
	@docker-compose down -v
	@docker-compose up -d postgres
	@echo "Waiting for database to be ready..."
	@sleep 30
	@echo "Generating xlarge dataset (this may take several minutes)..."
	@python3 database/seed-generator.py --preset xlarge \
		--db "postgresql://benchmark:benchmark123@localhost:5434/fraiseql_benchmark"
	@echo "✓ Xlarge dataset seeded"
	@make db-stats

# ============================================================================
# Database Statistics and Management
# ============================================================================

db-stats:
	@echo ""
	@echo "Database table statistics:"
	@echo "================================"
	@docker-compose exec -T postgres psql -U benchmark -d fraiseql_benchmark -c \
		"SELECT schemaname, tablename, n_live_tup as rows, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_stat_user_tables WHERE schemaname = 'benchmark' ORDER BY n_live_tup DESC;" || echo "Database not ready yet"
	@echo ""

clean-db:
	@echo "Cleaning database..."
	@docker-compose down -v
	@docker-compose up -d postgres
	@echo "Waiting for database initialization..."
	@sleep 10
	@echo "✓ Database cleaned and initialized"

# ============================================================================
# JMeter Dataset Generation
# ============================================================================

generate-datasets:
	@echo "Generating JMeter parameterized datasets..."
	@mkdir -p tests/perf/datasets
	@bash tests/perf/datasets/generate-datasets.sh

# ============================================================================
# Container Management
# ============================================================================

up:
	@docker-compose up -d
	@echo "Containers started. Waiting for health checks..."
	@sleep 10
	@docker-compose ps

down:
	@docker-compose down

logs:
	@docker-compose logs -f

ps:
	@docker-compose ps

# ============================================================================
# Utility Targets
# ============================================================================

# Verify schema is correctly initialized
schema-check:
	@echo "Verifying database schema..."
	@docker-compose exec -T postgres psql -U benchmark -d fraiseql_benchmark -c \
		"SELECT schemaname, COUNT(*) as table_count FROM pg_stat_user_tables WHERE schemaname = 'benchmark' GROUP BY schemaname;"

# Show first 5 records from each table
schema-sample:
	@echo "Sample data from benchmark tables:"
	@docker-compose exec -T postgres psql -U benchmark -d fraiseql_benchmark -c \
		"SELECT id, identifier, username, full_name FROM benchmark.tb_user LIMIT 3; SELECT id, identifier, title FROM benchmark.tb_post LIMIT 3; SELECT id, content FROM benchmark.tb_comment LIMIT 3;"

.PHONY: schema-check schema-sample
