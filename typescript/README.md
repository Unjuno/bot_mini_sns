# TypeScript standalone implementation

`src/common.ts` implements the same platform-neutral event and reply contract as
the Python, PHP, and Go ports. The TypeScript server independently handles
webhooks, persistence, platform adapters, and replies; it does not require
Python. Build with `npm install && npm run build`.
The webhook server persists events to SQLite (`posts.sqlite` by default); set
`TYPESCRIPT_DATABASE_PATH` to change the database path. Node.js 22.5 or later
is required because the runtime uses the built-in `node:sqlite` module.
