# ドキュメント一覧

## プロジェクト概要

このプロジェクトは、Python版・LINEを基準に複数プラットフォームと言語へ展開した**共存型マイクロSNSのMVP完成版**である。
Python版では対象17プラットフォームのアダプターを実装済みで、共通契約とオフライン検証を提供する。LINEは基準実装として扱う。
投稿一覧では投稿者名を表示せず、内容を中心に扱う。

現行MVPの実装・自動テスト・ローカルHTTPスモークテストは完了している。実サービスの接続は、利用者が各サービスの認証情報とWebhookを設定した後に確認する。

現行MVPの操作は固定フローのみとする。送信元プラットフォームとコンテンツ種別が一致する最新投稿を、各サービスの上限まで返す。

```text
コンテンツを送信 → 保存 → 同じ種類の最新コンテンツを最大数返信
```

キーワード、コマンド、検索、リッチメニュー、翻訳、広告は現行MVPおよび直近の実装対象外とする。

本体仕様の正本は [core-spec.md](core-spec.md) とする。
保留中のアイデアは [future-vision.md](future-vision.md) に分離し、現行MVPの仕様と混同しない。

| 資料 | 内容 |
| --- | --- |
| [architecture.md](architecture.md) | 複数サービスを共通Botとして扱う全体設計 |
| [core-spec.md](core-spec.md) | 確定したMVP本体仕様と拡張契約 |
| [future-vision.md](future-vision.md) | 保留中の将来アイデア（現行対象外） |
| [openapi.yaml](openapi.yaml) | 言語・サービス共通のHTTP/JSONインターフェース |
| [lean4-spec.md](lean4-spec.md) | Lean 4で固定フローを検証するためのモデル |
| [implementation-languages.md](implementation-languages.md) | 対応プログラミング言語とデプロイ方針 |
| [../formal/README.md](../formal/README.md) | Lean 4で実行できる形式証明 |
| [platform-research-2026-07-26.md](platform-research-2026-07-26.md) | プラットフォーム料金・利用条件の調査 |
| [content-batch-spec.md](content-batch-spec.md) | 同種コンテンツの直近一括返信とプラットフォーム差分 |
| [platforms/README.md](platforms/README.md) | プラットフォーム別の料金・使い方・適合性 |
| [user-flow.md](user-flow.md) | 利用者の操作フロー |
| [configuration.md](configuration.md) | 環境変数・設定ファイル・デプロイ設定 |
| [public-release-checklist.md](public-release-checklist.md) | 公開前の確認項目 |

## 実装設計（2026-07-26 確定）
 
- **MVPファースト**: 固定フローを `core/` に実装し、その上に機能を追加する
- **テスト分離**: coreはプラットフォーム非依存でテスト（ビューアイソレーション）
- **OV層**: OpenAPIスキーマに基づくPydanticバリデーションをアダプター境界に配置
- **参照OSSパターン**: FastAPI + Pydantic（型保証）、Hexagonal Architecture（層分離）
 
詳細は [architecture.md](architecture.md) を参照。

## 基本方針

このプロジェクトは、複数のチャットサービスを入口として利用できる小規模コミュニティ向けの共通Bot連携基盤を目指す。
