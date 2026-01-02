FROM golang:1.23-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git wget

# Copy go mod files
COPY go.mod go.sum* ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN go build -o server ./cmd/server

FROM alpine:latest

# Install runtime dependencies
RUN apk --no-cache add ca-certificates wget

WORKDIR /root/

# Copy the binary
COPY --from=builder /app/server .

EXPOSE 8080

CMD ["./server"]
