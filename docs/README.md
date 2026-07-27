# ドキュメント一覧

## プロジェクト概要

このプロジェクトは、Python版・LINEを基準に複数プラットフォームと言語へ展開する**共存型マイクロSNSの共通基盤**である。
LINE、Telegram、Discordなどの各サービスをSNS本体にするのではなく、各サービス上のBotを共通インターフェースとして利用する。利用者はどの対応サービスからでもBotへ投稿でき、Botが共通コアへ変換して保存・返信する。各Botを設定すれば、プラットフォーム間で投稿を共有してやり取りできる。
Python版では対象17プラットフォームの共通契約とオフライン検証を提供し、各サービス向けの接続骨格を持つ。実サービス対応の範囲は[プラットフォーム調査・実装照合](platform-implementation-audit.md)に整理する。LINEは基準実装として扱う。
なお、`python/app.py` はLINE専用の基準Webhook、`python/adapter_app.py` は各プラットフォームを共通コアへ接続するクロスプラットフォーム入口である。
投稿一覧では投稿者名を表示せず、内容を中心に扱う。

現行仕様の共通処理・自動テスト・ローカルHTTPスモークテストは完了している。本番接続として検証済みなのはLINEであり、その他のプラットフォームは未検証の本番起動を防ぐため、オフライン共通契約として扱う。

現行仕様の操作は固定フローのみとする。Botが受信した投稿を共通イベントへ変換し、プラットフォームをまたいでコンテンツ種別が一致する最新投稿を、返信先サービスの上限まで返す。

```text
利用者 → 各サービス上のBot → 共通コアで保存 → Botが返信
```

キーワード、コマンド、検索、リッチメニュー、翻訳、広告は現行仕様および直近の実装対象外とする。

本体仕様の正本は [core-spec.md](core-spec.md) とする。
保留中のアイデアは [future-vision.md](future-vision.md) に分離し、現行仕様と混同しない。

| 資料 | 内容 |
| --- | --- |
| [architecture.md](architecture.md) | 複数サービスを共通Botとして扱う全体設計 |
| [core-spec.md](core-spec.md) | 確定した本体仕様と拡張契約 |
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
| [development.md](development.md) | 開発環境・検証・実装境界 |
| [public-release-checklist.md](public-release-checklist.md) | 公開前の確認項目 |

## 実装設計（2026-07-26 確定）
 
- **固定フローを中心にする**: 固定フローを `core/` に実装し、その上に機能を追加する
- **テスト分離**: coreはプラットフォーム非依存でテスト（ビューアイソレーション）
- **OV層**: OpenAPIスキーマに基づくPydanticバリデーションをアダプター境界に配置
- **参照OSSパターン**: FastAPI + Pydantic（型保証）、Hexagonal Architecture（層分離）
 
詳細は [architecture.md](architecture.md) を参照。

## 基本方針

このプロジェクトは、複数のチャットサービスを入口として利用できる小規模コミュニティ向けの共通Bot連携基盤を目指す。
