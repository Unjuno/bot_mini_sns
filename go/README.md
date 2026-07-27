# Go common implementation

`common.go` provides the same platform-neutral event/reply contract as the
Python, PHP, and TypeScript ports. Platform-specific webhook and API adapters
are intentionally separate from this package.
Run the normalized webhook server with `go run .`; it listens on `/webhook` and uses `PORT` (default `8080`).
