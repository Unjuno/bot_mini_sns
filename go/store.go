package common

import (
	"database/sql"
	"fmt"

	_ "modernc.org/sqlite"
)

// PostStore is the persistent store used by the standalone Go runtime.
type PostStore struct{ db *sql.DB }

func OpenPostStore(path string) (*PostStore, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	const schema = `CREATE TABLE IF NOT EXISTS platform_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        user_id TEXT NOT NULL,
        content_type TEXT NOT NULL,
        text TEXT,
        media_url TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )`
	if _, err = db.Exec(schema); err != nil {
		_ = db.Close()
		return nil, err
	}
	return &PostStore{db: db}, nil
}

func (s *PostStore) Close() error { return s.db.Close() }

func (s *PostStore) ProcessEvent(event InboundEvent, limit int) (OutboundReply, error) {
	if !isSupportedPlatform(event.Platform) {
		return OutboundReply{}, fmt.Errorf("unsupported platform: %s", event.Platform)
	}
	if event.UserID == "" || event.ContentType == "" {
		return OutboundReply{}, fmt.Errorf("platform, user_id, and content_type are required")
	}
	if event.ContentType != "text" && event.ContentType != "image" && event.ContentType != "audio" && event.ContentType != "video" && event.ContentType != "file" {
		return OutboundReply{}, fmt.Errorf("unsupported content type: %s", event.ContentType)
	}
	if limit < 1 {
		return OutboundReply{}, fmt.Errorf("limit must be a positive integer")
	}
	tx, err := s.db.Begin()
	if err != nil {
		return OutboundReply{}, err
	}
	defer tx.Rollback()
	if _, err = tx.Exec(`INSERT INTO platform_posts (platform,user_id,content_type,text,media_url) VALUES (?,?,?,?,?)`, event.Platform, event.UserID, event.ContentType, event.Text, event.MediaURL); err != nil {
		return OutboundReply{}, err
	}
	rows, err := tx.Query(`SELECT content_type,text,media_url FROM platform_posts WHERE content_type=? ORDER BY id DESC LIMIT ?`, event.ContentType, limit)
	if err != nil {
		return OutboundReply{}, err
	}
	defer rows.Close()
	result := OutboundReply{}
	for rows.Next() {
		var message OutboundMessage
		if err := rows.Scan(&message.Type, &message.Text, &message.MediaURL); err != nil {
			return OutboundReply{}, err
		}
		result.Messages = append(result.Messages, message)
	}
	if err := rows.Err(); err != nil {
		return OutboundReply{}, err
	}
	if err := tx.Commit(); err != nil {
		return OutboundReply{}, err
	}
	return result, nil
}
