# Railway Deployment Guide

This bot can run locally without Railway. Railway is only used to host the Flask application on a public HTTPS URL so that LINE can call the webhook.

## 1. Create a Railway service

1. Create a new Railway project.
2. Deploy from the GitHub repository `Unjuno/line_bot_mini_sns`.
3. Use the `main` branch.
4. Railway detects the Python project from `requirements.txt`.

## 2. Start command

Set the service start command to:

```bash
gunicorn -w 1 app:app
```

Railway provides the `PORT` environment variable. The application already reads it when running with `python app.py`.

## 3. Environment variables

Add these variables in Railway. Never commit the real values to GitHub.

```env
ACCESS_TOKEN=your_line_channel_access_token
CHANNEL_SECRET=your_line_channel_secret
CONFIG_PATH=config.json
DATABASE_PATH=sns_bot.db
MEDIA_DIR=uploaded_media
MEDIA_BASE_URL=https://your-railway-domain
```

`MEDIA_BASE_URL` is required when images, audio, video, or files are returned to users. It must be a public HTTPS URL.

## 4. Public domain and LINE webhook

After deployment, generate or assign a Railway public domain. Then set the LINE Developers webhook URL to:

```text
https://your-railway-domain/callback
```

Enable webhook usage and verify the webhook from the LINE Developers console.

## 5. Storage warning

The default SQLite database and `uploaded_media` directory are local files. They are suitable for testing and small communities, but may not survive redeployments or restarts depending on the Railway storage setup.

For a larger community, use:

- Railway PostgreSQL for users, posts, and read records
- S3-compatible storage or Cloudflare R2 for media files
- A persistent volume only when its backup and restore behavior is understood

## 6. Local execution

Railway is not required for local execution:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

For LINE to reach a local server, use an HTTPS tunnel such as ngrok and set the webhook URL to the tunnel URL plus `/callback`.
