# Go standalone implementation

`common.go` provides the same platform-neutral event/reply contract as the
Python, PHP, and TypeScript ports. The Go server independently handles
webhooks, persistence, platform adapters, and replies; it does not require
Python. Platform-specific adapters remain separate from this package.
Run the normalized webhook server with `go run ./cmd/server`; it listens on `/webhook` and uses `PORT` (default `8080`).
Events are persisted to `posts.json`; set `POSTS_FILE` to change the path.
