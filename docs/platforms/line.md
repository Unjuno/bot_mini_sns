# LINE

調査日：2026年7月26日

## 料金

日本のLINE公式アカウントは、コミュニケーションプラン月額0円・月200通、ライト月5,000円・5,000通、スタンダード月15,000円・30,000通。Reply APIの応答メッセージは料金通数にカウントされないため、今回のReply専用方式では送信通数の面で実質無制限。

## 使い方

LINE公式アカウントを作成し、Messaging APIチャネルとWebhook URLを設定する。Webhookイベントの`replyToken`を使い、Reply APIで返信する。Reply Tokenは1回のみ、原則Webhook受信後1分以内に使用する。

## ADKomeとの適合

文章・写真・音声・動画・ファイルを受信でき、保存後に受信した種類と同じ最新投稿を最大5件、投稿単位のメッセージで返信する固定フローに適合する。1回のReply APIは最大5メッセージ。

## 公式情報

- https://developers.line.biz/ja/docs/messaging-api/pricing/
- https://developers.line.biz/ja/reference/messaging-api/nojs/
