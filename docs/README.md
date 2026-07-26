# ドキュメント一覧

## プロジェクト概要

このプロジェクトは、Python版・LINE連携を現行スコープとする**共存型マイクロSNS**である。
Telegram、Discord、Zulipなどは将来拡張として設計資料に記載するが、現行実装の対象外とする。
投稿一覧では投稿者名を表示せず、内容を中心に扱う。

現行MVPの操作は固定フローのみとする。送信元プラットフォームとコンテンツ種別が一致する最新投稿を、各サービスの上限まで返す。

```text
コンテンツを送信 → 保存 → 同じ種類の最新コンテンツを最大数返信
```

キーワード、コマンド、検索、リッチメニューは現行MVPの必須機能ではない。将来の追加機能も翻訳と広告に限定する。

本体仕様の正本は [core-spec.md](core-spec.md) とする。
将来構想は [future-vision.md](future-vision.md) に分離し、現行MVPの必須仕様と混同しない。

| 資料 | 内容 |
| --- | --- |
| [architecture.md](architecture.md) | 複数サービスを共通Botとして扱う全体設計 |
| [core-spec.md](core-spec.md) | 確定したMVP本体仕様と拡張契約 |
| [future-vision.md](future-vision.md) | 翻訳・広告の将来構想 |
| [openapi.yaml](openapi.yaml) | 言語・サービス共通のHTTP/JSONインターフェース |
| [lean4-spec.md](lean4-spec.md) | Lean 4で固定フローを検証するためのモデル |
| [implementation-languages.md](implementation-languages.md) | 対応プログラミング言語とデプロイ方針 |
| [../formal/README.md](../formal/README.md) | Lean 4で実行できる形式証明 |
| [platform-research-2026-07-26.md](platform-research-2026-07-26.md) | プラットフォーム料金・利用条件の調査 |
| [content-batch-spec.md](content-batch-spec.md) | 同種コンテンツの直近一括返信とプラットフォーム差分 |
| [platforms/README.md](platforms/README.md) | プラットフォーム別の料金・使い方・適合性 |
| [user-flow.md](user-flow.md) | 利用者の操作フロー |

## 実装設計（2026-07-26 確定）
 
- **MVPファースト**: 固定フローを `core/` に実装し、その上に機能を追加する
- **テスト分離**: coreはプラットフォーム非依存でテスト（ビューアイソレーション）
- **OV層**: OpenAPIスキーマに基づくPydanticバリデーションをアダプター境界に配置
- **参照OSSパターン**: FastAPI + Pydantic（型保証）、Hexagonal Architecture（層分離）
 
詳細は [architecture.md](architecture.md) を参照。

## 基本方針

このプロジェクトは、複数のチャットサービスを入口として利用できる小規模コミュニティ向けの共通Bot連携基盤を目指す。
