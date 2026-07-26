# Bluesky

調査日：2026年7月26日

## 料金

API利用料は基本的にない。レート制限、PDSや運用環境の費用は別途確認する。

## 使い方

AT Protocolのアカウントで認証し、投稿・返信APIを呼び出す。Bot向けのカスタム動作やフィードも作成できる。受信イベントを待つチャットBotとはイベント設計が異なる。

## ADKomeとの適合

SNS型の投稿・返信先として有望。ただし、入力をBotへ送り、その場でタイムラインを返す用途には追加の通知・購読設計が必要。

## 公式情報

- https://docs.bsky.app/docs/tutorials/creating-a-post
- https://docs.bsky.app/
