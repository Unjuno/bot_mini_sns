# Telegram

調査日：2026年7月26日

## 料金

Bot PlatformとBot APIは無料。サーバー、データベース、メディア保存費用は別途必要。大量ブロードキャストなど有料機能は今回の対象外。

## 使い方

@BotFatherでBotを作成し、Bot Tokenを環境変数へ保存する。Webhookまたは`getUpdates`でUpdateを受け、`sendMessage`や`sendPhoto`などで返信する。ユーザーが先にBotへ入力する必要がある。

## ADKomeとの適合

文章・写真・音声・動画・ファイルに対応しやすく、LINEに次ぐ追加候補。Media Groupは2〜10件をまとめて送信できるため、最新5件の返信に余裕がある。

## 公式情報

- https://core.telegram.org/bots
- https://core.telegram.org/bots/api
