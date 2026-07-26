# Mastodon

調査日：2026年7月26日

## 料金

API利用料は基本的にない。既存インスタンスを使う場合は運営者の条件、自前運用ではサーバー・ストレージ費用が必要。

## 使い方

対象インスタンスでアプリとアクセストークンを作成する。Streaming APIで投稿・通知を受信し、Status APIで投稿・返信する。Webhook型ではなくストリーミング接続の維持が必要。

## ADKomeとの適合

SNS・タイムライン型で本体構想との相性が非常に良い。文章・画像・音声・動画・ファイルをメディア添付として扱える。チャットBot型とは別のSNSアダプターとして設計する。

## 公式情報

- https://docs.joinmastodon.org/methods/streaming/
- https://docs.joinmastodon.org/methods/statuses/
