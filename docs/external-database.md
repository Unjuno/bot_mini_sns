# 外部データベースへの切り替え

各言語版は、ローカル開発ではSQLiteを使用します。公開環境や複数インスタンスで運用する場合は、SQLiteファイルではなく外部データベースを使用してください。

このリポジトリの標準実装はSQLiteです。Pythonの共通Webhookサーバーは`DATABASE_URL`、Go版は`GO_DATABASE_URL`、PHP版は`PHP_DATABASE_URL`でPostgreSQLへ切り替えられます。TypeScript版は引き続きSQLite実装で、同じRepository契約を保った外部DB実装が必要です。推奨DBはPostgreSQLです。

## なぜ外部DBが必要か

SQLiteファイルをアプリケーション内に置く方式は、単一プロセスのローカル実行には適しています。しかし、次の環境ではデータが失われたり、同時書き込みで問題が起きたりします。

- コンテナを再作成するデプロイ
- 永続ディスクを持たないホスティング
- 複数のBotプロセス・複数インスタンスでの運用
- 自動スケールする環境

## 共通で満たす契約

外部DB版は、SQLite版と同じ`platform_posts`テーブルと処理結果を提供してください。

```sql
CREATE TABLE platform_posts (
    id BIGSERIAL PRIMARY KEY,
    platform TEXT NOT NULL,
    user_id TEXT NOT NULL,
    content_type TEXT NOT NULL,
    text TEXT,
    media_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX platform_posts_content_type_id_idx
    ON platform_posts (content_type, id DESC);
```

投稿処理は次の順序で行います。

1. 受信イベントを検証する
2. 投稿をINSERTする
3. `content_type`が同じ投稿を`id DESC`で取得する
4. プラットフォームごとの返信上限を適用する
5. 返信を作成する
6. INSERTと取得を同一トランザクションで確定する

`platform`や`user_id`を検索条件に含めない点は重要です。このシステムはプラットフォーム間で投稿を共有します。

## 接続設定

実装側では、SQLite用のパスとは別に、次の環境変数を受け取る方式を推奨します。

```text
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require
```

`DATABASE_URL`が設定されている場合、Pythonの`adapter_app.py`はPostgreSQLを使用し、`GO_DATABASE_URL`が設定されている場合、Goサーバー、`PHP_DATABASE_URL`が設定されている場合、PHPサーバーもPostgreSQLを使用します。未設定の場合はSQLiteへフォールバックします。接続文字列やパスワードは`.env.example`に実値を記載せず、ホスティングのSecret設定へ登録してください。Python依存関係には`psycopg[binary]`、Go依存関係には`pgx`が含まれます。PHPはPDO PostgreSQL拡張が必要です。

## 言語別の実装方針

| 言語 | PostgreSQL接続の候補 | 既存のSQLite実装 |
| --- | --- | --- |
| Python | `psycopg`、SQLAlchemy | `python/core/service.py`、`sqlite3` |
| TypeScript | `pg`、Prisma、Drizzle | `typescript/src/common.ts`、`node:sqlite` |
| Go | `pgx`、`database/sql`対応ドライバー | `go/store.go`、`modernc.org/sqlite` |
| PHP | PDO PostgreSQL、Doctrine DBAL | `php/src/common.php`、PDO SQLite |

各言語版で外部DB対応を実装する場合は、SQLiteリポジトリを直接書き換えるのではなく、同じ`PostStore`／Repository契約の実装を追加してください。SQLiteとPostgreSQLのSQL差、プレースホルダー、トランザクション、接続プールを各言語の標準的な方法で処理します。

## 移行手順

1. PostgreSQLインスタンスを作成する
2. `DATABASE_URL`をSecretとして登録する
3. 上記スキーマをマイグレーションで適用する
4. 起動時に接続確認とスキーマ確認を行う
5. 共通イベントを送信し、投稿の保存とプラットフォーム間返信を確認する
6. SQLiteから移行する場合は、`platform_posts`をエクスポートしてPostgreSQLへインポートする
7. SQLiteファイルを削除する前に、件数と最新投稿を照合する

本番で外部DBを使用する場合でも、SQLiteを削除するだけでは切り替わりません。各言語版のDBアダプター、マイグレーション、接続設定を実装してからデプロイしてください。
