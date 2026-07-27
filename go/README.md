# Go standalone implementation

`common.go` provides the same platform-neutral event/reply contract as the
Python, PHP, and TypeScript ports. The Go server independently handles
webhooks, persistence, platform adapters, and replies; it does not require
Python. Platform-specific adapters remain separate from this package.
Run the normalized webhook server with `go run ./cmd/server`; it listens on `/webhook` and uses `PORT` (default `8080`).
Events are persisted to SQLite (`posts.sqlite` by default); set
`GO_DATABASE_PATH` to change the path. The Go runtime uses the pure-Go
`modernc.org/sqlite` driver and does not require CGO.
