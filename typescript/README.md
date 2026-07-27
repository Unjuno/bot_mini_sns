# TypeScript common implementation

`src/common.ts` implements the same platform-neutral event and reply contract as
the Python and PHP ports. Build with `npm install && npm run build`.
The webhook server persists events to `posts.json`; set `POSTS_FILE` to change the path.
