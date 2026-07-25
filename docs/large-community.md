# Large Community Operation Plan

This document describes the changes required before using the bot with a larger community.
The current implementation is an MVP and is suitable for development or a small group.

## Current MVP limitations

- SQLite is stored in a local file and is not suitable for multiple application instances.
- Media files are stored on the local filesystem and may disappear after a Render restart.
- A timeline request returns at most five LINE messages in the current implementation.
- There is no rate limiting, moderation queue, reporting workflow, or administrator dashboard yet.
- User display names, media cleanup, and operational metrics need stronger production handling.

## Recommended production architecture

```text
LINE Messaging API
        |
        v
Flask application on Render
        |
        +-- PostgreSQL: users, posts, reads, moderation, audit logs
        +-- Object storage: images, audio, video, and files
        +-- Optional Redis/queue: background jobs and rate limiting
```

## Required changes by priority

### Priority 1: data safety

- Move users, posts, and read records from SQLite to PostgreSQL.
- Move uploaded media from `MEDIA_DIR` to object storage such as S3-compatible storage or Cloudflare R2.
- Store media metadata, file size, MIME type, checksum, and storage key in the database.
- Add database migrations instead of relying only on startup schema creation.
- Add backups and a restore procedure.

### Priority 2: community safety

- Add administrator accounts and role checks.
- Add post deletion, user suspension, and report handling.
- Add text length, file size, MIME type, and daily post limits.
- Add rate limiting per user and per LINE event.
- Do not log message bodies, tokens, or private media URLs.

### Priority 3: LINE and application reliability

- Keep Pull-based timeline retrieval as the default to control message costs.
- Split large timelines into multiple user requests instead of exceeding LINE reply limits.
- Handle duplicate webhook events using the LINE event ID or message ID.
- Return quickly from the webhook and move expensive media processing to a background job.
- Add structured logs, error monitoring, health checks, and request IDs.

### Priority 4: user experience

- Use a Rich Menu for `新着`, `投稿`, `使い方`, and `退会`.
- Add pagination commands such as `次へ` and `前へ`.
- Add community name and description settings.
- Add optional replies, reactions, and reports through configuration flags.
- Add an onboarding message explaining privacy and media retention.

## Suggested capacity settings

The following values are starting points, not hard limits:

| Setting | Small group | Larger community |
| --- | ---: | ---: |
| Posts per timeline request | 5 | 5 |
| Maximum text length | 500 | 500 |
| Maximum daily posts per user | 20 | 10 |
| Image size | 10 MB | 10 MB |
| Video size | 50 MB | 50 MB |
| Media retention | 30 days | 30 days, then archive/delete |

## Deployment checklist

- Set `ACCESS_TOKEN` and `CHANNEL_SECRET` only in Render environment variables.
- Set `MEDIA_BASE_URL` only when the media endpoint is protected and suitable for public LINE access.
- Configure a persistent database and object storage before enabling media for a large group.
- Configure the LINE webhook URL as `https://<render-domain>/callback`.
- Verify webhook signature validation and duplicate event handling.
- Test registration, every enabled content type, timeline paging, deletion, and suspension.
- Monitor database size, storage size, error rate, and LINE API errors.

## Migration order

1. Keep the current Pull-based behavior and add limits and duplicate-event protection.
2. Introduce PostgreSQL behind a repository/data-access layer.
3. Introduce object storage and migrate existing media.
4. Add moderation and administrator operations.
5. Add pagination and Rich Menu actions.
6. Load-test with the expected number of users and daily posts.
