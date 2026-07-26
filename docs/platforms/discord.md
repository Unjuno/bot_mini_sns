# Discord

調査日：2026年7月26日

## 料金

Bot API自体の個別利用料は基本的にない。Botを動かすサーバー費用と、参加先サーバーの運用条件は別途必要。

## 使い方

Developer Portalでアプリ・Botを作成し、対象サーバーへ招待する。GatewayイベントまたはInteractionsを受信して、チャンネルへメッセージを送る。本文や添付の取得には権限・`MESSAGE_CONTENT` intentの確認が必要。

## ADKomeとの適合

コミュニティ型に強く、文章・写真・音声・動画・ファイルに対応できる。1メッセージに最大10 embeds、ファイル送信はリクエスト25MiB制限がある。個人SNSよりサーバー・チャンネル型。

## 公式情報

- https://docs.discord.com/developers/platform/bots
- https://docs.discord.com/developers/resources/message
