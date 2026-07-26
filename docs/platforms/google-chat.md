# Google Chat

調査日：2026年7月26日

## 料金

Chat API自体の一律料金は確認できない。Google Cloudプロジェクト、認証、Workspace契約やCloud利用条件を確認する。

## 使い方

Google Chatアプリを作成し、インタラクションイベントを受信する。`MESSAGE`イベントに対して同期レスポンスを返し、添付はAPIから取得する。

## ADKomeとの適合

Workspace利用者向け。文章・添付ファイルには対応しやすいが、一般公開型のSNS入口としては認証・Cloud設定が重い。

## 公式情報

- https://developers.google.com/workspace/chat/receive-respond-interactions
- https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces.messages.attachments
