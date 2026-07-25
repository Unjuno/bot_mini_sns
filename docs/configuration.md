# Configuration Guide

The bot uses two types of configuration:

- `.env`: secrets and environment-specific paths
- `config.json`: feature switches and application behavior

## Environment variables

Copy `.env.example` to `.env` and replace the placeholder values.

| Variable | Required | Description |
| --- | --- | --- |
| `ACCESS_TOKEN` | Yes | LINE Messaging API channel access token |
| `CHANNEL_SECRET` | Yes | LINE Messaging API channel secret |
| `CONFIG_PATH` | No | Path to the JSON configuration file. Defaults to `config.json`. |
| `DATABASE_PATH` | No | SQLite database path. Defaults to `sns_bot.db`. |
| `MEDIA_DIR` | No | Directory for downloaded media files. Defaults to `uploaded_media`. |
| `MEDIA_BASE_URL` | Required for media retrieval | Public HTTPS base URL used by LINE to retrieve images, audio, and video. |

Example:

```env
ACCESS_TOKEN=replace_with_your_line_access_token
CHANNEL_SECRET=replace_with_your_line_channel_secret
MEDIA_BASE_URL=https://your-public-domain.example
```

`MEDIA_BASE_URL` must be reachable from the public internet. `localhost` and `127.0.0.1` cannot be used when LINE needs to retrieve media.

## Application configuration

The default sample is [config.example.json](../config.example.json). Copy it to `config.json` before starting the bot.

### `features`

| Key | Description |
| --- | --- |
| `registration` | Allows new users to register automatically. |
| `text_post` | Enables text posts. |
| `post_fetch` | Enables Pull-based retrieval through `新着` or `タイムライン`. |

### `timeline`

| Key | Description |
| --- | --- |
| `include_author_posts` | Includes the current user's own posts in their timeline. |
| `posts_per_request` | Maximum number of posts returned for one request. |
| `mark_as_read` | Records posts as read after they are returned. |

### `media`

| Key | Description |
| --- | --- |
| `enabled_types` | Enables media types such as `image`, `audio`, `video`, `file`, and `location`. |
| `retention_days` | Intended retention period for stored media. Cleanup jobs are not automatic yet. |

## LINE setup

Set the LINE webhook URL to:

```text
https://your-public-domain.example/callback
```

Keep `.env` private. Do not commit it to source control.
