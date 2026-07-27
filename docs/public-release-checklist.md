# 公開前チェックリスト

## 設定と秘密情報

- [x] `.env.example`に秘密情報の実値が入っていない
- [x] `.env`、SQLite、`posts.json`、アップロードファイルがGit管理外になっている
- [x] `python/check_setup.py --platform <platform> --offline`が成功する
- [x] `docs/platforms/README.md`の必須環境変数と`.env.example`が一致している

## 動作確認

- [x] Pythonテストが成功する
- [x] Flaskの起動確認が成功する
- [x] TypeScriptのビルドと型チェックが成功する
- [x] Goテストが成功する
- [x] PHP構文チェックが成功する
- [x] 認証なしWebhookで保存と返信を確認する
- [ ] 実サービスを使う場合は、利用するサービスだけ実アクセストークンでWebhookと返信を確認する
- [x] 未検証プラットフォームを本番モードで起動しない

## 公開設定

- [x] `LICENSE`の内容を確認する
- [x] READMEの起動・設定手順を確認する
- [x] GitHub Actionsの検証定義を確認する
- [x] `git status`がcleanである
- [x] GitHubのリポジトリVisibilityがPrivateのままであることを確認する

実サービスの認証情報がない場合でも、認証なしの共通契約テストまでは実行できます。実サービス接続の未確認項目は、公開後もREADMEやIssueで明示してください。
