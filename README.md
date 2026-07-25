# LINE Mini SNS

A **mini social network** built as a LINE Messaging API bot.
Users post text, images, audio, video, files, and locations — other users fetch the latest unread posts on demand.

Uses Pull-based timeline retrieval with `reply_message`; this avoids automatic Push delivery and helps reduce messaging charges.

> 🇯🇵 日本語のLINE Botです。登録ユーザー間でテキスト・画像・音声・動画・ファイル・位置情報を共有できます。

---

## Features

| Post Type | Support | Timeline Display |
|-----------|---------|-----------------|
| Text | ✅ | `TextSendMessage` |
| Image | ✅ | `ImageSendMessage` |
| Audio | ✅ | `AudioSendMessage` |
| Video | ✅ | `VideoSendMessage` |
| File | ✅ | Fallback text link |
| Location | ✅ | `LocationSendMessage` |
| Sticker | ✅ | `StickerSendMessage` |

- **Registration**: Users join by following the bot or sending "登録"
- **Unread tracking**: Each user sees only new posts since their last fetch
- **Config-driven**: Feature flags in `config.json` — disable media types, toggle registration
- **Config-driven**: Feature flags in `config.json` — disable media types, toggle registration

---

## How It Works

```
User → send message → LINE Platform → webhook → Flask server → SQLite
User → "新着"        → LINE Platform → webhook → Flask server → fetch unread posts → reply
```

All replies use `reply_message()` — free and unlimited under the LINE Messaging API free plan.

---

## Commands

| Input | Action |
|-------|--------|
| Any text | Post as text message |
| `新着` / `タイムライン` | Fetch unread posts |
| `登録` | Register (if registration is enabled) |
| `退会` | Delete your account |
| `使い方` / `ヘルプ` | Show help |

---

## Getting Started

### Prerequisites

- Python 3.10+
- A [LINE Developers](https://developers.line.biz/) account with a Messaging API channel
- (Optional) A [Render](https://render.com/) account for deployment

### 1. Clone

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Environment Variables

Create a `.env` file:

```env
ACCESS_TOKEN=your_line_channel_access_token
CHANNEL_SECRET=your_line_channel_secret
```

> **For Render**: Set these as Environment Variables in the Render dashboard instead of using `.env`.

### 3. Install

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 4. Configure

Edit `config.json` to enable/disable features:

```json
{
  "features": {
    "registration": true,
    "text_post": true,
    "post_fetch": true
  },
  "media": {
    "enabled_types": ["image", "audio", "video", "file", "location", "sticker"],
    "retention_days": 30
  }
}
```

### 5. Run

```bash
python app.py
```

### Run tests

```bash
python -m unittest discover -s tests -v
```

### 6. Set up LINE Webhook

1. Deploy or use [ngrok](https://ngrok.com/) for local HTTPS: `ngrok http 5000`
2. In [LINE Developers Console](https://developers.line.biz/console/), set Webhook URL to `https://your-domain/callback`
3. Enable webhook

---

## Deployment (Render)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Create a **Web Service** on Render
2. Connect your repository
3. Set:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 1 app:app`
4. Add Environment Variables:
   - `ACCESS_TOKEN`
   - `CHANNEL_SECRET`
   - `MEDIA_BASE_URL` → `https://your-app.onrender.com`
   - `CONFIG_PATH` → optional, defaults to `config.json`
   - `DATABASE_PATH` → optional, defaults to `sns_bot.db`
   - `MEDIA_DIR` → optional, defaults to `uploaded_media`
5. Deploy

> **Free tier note**: Render's free plan uses ephemeral storage. Data is lost on restart/deploy. The app handles this gracefully — old data is simply gone, new data starts fresh.

---

## Configuration (`config.json`)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `features.registration` | bool | `true` | Allow new user registration |
| `features.text_post` | bool | `true` | Allow text posts |
| `features.post_fetch` | bool | `true` | Enable "新着" timeline fetching |
| `timeline.include_author_posts` | bool | `true` | Include own posts in timeline |
| `timeline.posts_per_request` | int | `5` | Max posts returned per fetch |
| `media.enabled_types` | array | `[...]` | Allowed media types |
| `media.retention_days` | int | `30` | Media file retention (not yet enforced) |

---

## Project Structure

```
├── app.py              # Main Flask application
├── config.json         # Feature flags & settings
├── requirements.txt    # Python dependencies
├── .env                # Local environment variables (git-ignored)
├── .gitignore
├── README.md
├── docs/
│   ├── 仕様書.md       # Canonical product specification (Japanese)
│   ├── configuration.md # Configuration guide (English)
│   └── large-community.md # Production scaling plan
├── uploaded_media/     # Uploaded media files (git-ignored)
└── sns_bot.db          # SQLite database (git-ignored)
```

---

## Database

### `users`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| line_user_id | TEXT | LINE user ID (unique) |
| display_name | TEXT | Display name |
| status | TEXT | `active` or `deleted` |
| created_at | TEXT | ISO 8601 |
| updated_at | TEXT | ISO 8601 |

### `posts`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | Foreign key → users |
| type | TEXT | `text`, `image`, `audio`, `video`, `file`, `location`, `sticker` |
| text | TEXT | Message body or title |
| media_url | TEXT | URL for media content |
| mime_type | TEXT | MIME type |
| duration_ms | INTEGER | Audio duration |
| address | TEXT | Location address |
| latitude | REAL | Location latitude |
| longitude | REAL | Location longitude |
| status | TEXT | `published` or `deleted` |
| created_at | TEXT | ISO 8601 |

### `post_reads`
Tracks which posts each user has already seen.

---

## Cost

| Service | Cost |
|---------|------|
| LINE Messaging API | Reply messages are not counted as broadcast messages; account plan limits still apply |
| Render (free tier) | **Free** (ephemeral storage) |
| Storage | Auto-limited via retention |

Actual total depends on hosting, storage, and the LINE Official Account plan.

---

## Roadmap

- [x] Text posts
- [x] Image posts
- [x] Audio / Video / File / Location posts
- [x] Unread post tracking
- [x] Config-driven feature flags
- [ ] Media retention enforcement
- [ ] Admin commands
- [ ] LIFF timeline viewer
- [ ] i18n (English bot replies)

---

## License

MIT
