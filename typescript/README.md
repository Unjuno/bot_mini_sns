# TypeScript standalone implementation

`src/common.ts` implements the same platform-neutral event and reply contract as
the Python, PHP, and Go ports. The TypeScript server independently handles
webhooks, persistence, platform adapters, and replies; it does not require
Python. Build with `npm install && npm run build`.
The webhook server persists events to `posts.json`; set `POSTS_FILE` to change the path.
