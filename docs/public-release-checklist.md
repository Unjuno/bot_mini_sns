# 公開前チェックリスト

## 設定と秘密情報

- [ ] `.env.example`に秘密情報の実値が入っていない
- [ ] `.env`、SQLite、`posts.json`、アップロードファイルがGit管理外になっている
- [ ] `python/check_setup.py --platform <platform>`が成功する
- [ ] `python/check_setup.py --platform <platform> --offline`が成功する
- [ ] `docs/platforms/README.md`の必須環境変数と`.env.example`が一致している

## 動作確認

- [ ] Pythonテストが成功する
- [ ] Flaskの起動確認が成功する
- [ ] TypeScriptの型チェックが成功する
- [ ] Goテストが成功する
- [ ] PHP構文チェックが成功する
- [ ] 認証なしWebhookで保存と返信を確認する
- [ ] 実サービスを使う場合は、利用するサービスだけ実アクセストークンでWebhookと返信を確認する

## 公開設定

- [ ] `LICENSE`の内容を確認する
- [ ] READMEの起動・設定手順を確認する
- [ ] GitHub Actionsが成功している
- [ ] `git status`がcleanである
- [ ] GitHubのリポジトリVisibilityが意図した状態である

実サービスの認証情報がない場合でも、認証なしの共通契約テストまでは実行できます。実サービス接続の未確認項目は、公開後もREADMEやIssueで明示してください。
