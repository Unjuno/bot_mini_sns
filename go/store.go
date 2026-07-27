package common

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"

	_ "github.com/jackc/pgx/v5/stdlib"
	_ "modernc.org/sqlite"
)

// PostStore is the persistent store used by the standalone Go runtime.
type PostStore struct{ db *sql.DB }

func OpenPostStore(path string) (*PostStore, error) {
	driver, schema := "sqlite", `CREATE TABLE IF NOT EXISTS platform_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, platform TEXT NOT NULL, user_id TEXT NOT NULL,
        content_type TEXT NOT NULL, text TEXT, media_url TEXT, status TEXT NOT NULL DEFAULT 'published',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )`
	if strings.HasPrefix(path, "postgres://") || strings.HasPrefix(path, "postgresql://") {
		driver = "pgx"
		schema = `CREATE TABLE IF NOT EXISTS platform_posts (
        id BIGSERIAL PRIMARY KEY, platform TEXT NOT NULL, user_id TEXT NOT NULL,
        content_type TEXT NOT NULL, text TEXT, media_url TEXT, status TEXT NOT NULL DEFAULT 'published',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )`
	}
	db, err := sql.Open(driver, path)
	if err != nil {
		return nil, err
	}
	if _, err = db.Exec(schema); err != nil {
		_ = db.Close()
		return nil, err
	}
	if driver == "sqlite" {
		_, _ = db.Exec("ALTER TABLE platform_posts ADD COLUMN status TEXT NOT NULL DEFAULT 'published'")
	}
	if _, err = db.Exec(`CREATE TABLE IF NOT EXISTS processed_events (fingerprint TEXT PRIMARY KEY, response_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`); err != nil {
		_ = db.Close()
		return nil, err
	}
	return &PostStore{db: db}, nil
}

func (s *PostStore) ClaimEvent(fingerprint string) (*OutboundReply, error) {
	var raw string
	err := s.db.QueryRow("SELECT response_json FROM processed_events WHERE fingerprint=?", fingerprint).Scan(&raw)
	if err == nil {
		var reply OutboundReply
		if err := json.Unmarshal([]byte(raw), &reply); err != nil {
			return nil, err
		}
		return &reply, nil
	}
	if err != sql.ErrNoRows {
		return nil, err
	}
	_, err = s.db.Exec("INSERT INTO processed_events (fingerprint,response_json) VALUES (?,?)", fingerprint, `{"messages":[]}`)
	return nil, err
}

func (s *PostStore) CompleteEvent(fingerprint string, reply OutboundReply) error {
	raw, err := json.Marshal(reply)
	if err != nil {
		return err
	}
	_, err = s.db.Exec("UPDATE processed_events SET response_json=? WHERE fingerprint=?", string(raw), fingerprint)
	return err
}

func (s *PostStore) ReleaseEvent(fingerprint string) error {
	_, err := s.db.Exec("DELETE FROM processed_events WHERE fingerprint=?", fingerprint)
	return err
}

func (s *PostStore) SoftDeletePost(id int64) (bool, error) {
	result, err := s.db.Exec("UPDATE platform_posts SET status='deleted' WHERE id=? AND status!='deleted'", id)
	if err != nil {
		return false, err
	}
	count, err := result.RowsAffected()
	return count > 0, err
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
	rows, err := tx.Query(`SELECT content_type,text,media_url FROM platform_posts WHERE content_type=? AND status='published' ORDER BY id DESC LIMIT ?`, event.ContentType, limit)
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
