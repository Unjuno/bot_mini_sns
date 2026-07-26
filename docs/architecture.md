# 共通Bot連携基盤の構成

## プロジェクトの位置づけ

このプロジェクトは、LINEやTelegramなどの大手プラットフォームを置き換えるものではない。
それらと共存し、Botを入口として小さなコミュニティ向けのSNS機能を提供する。

```text
大手チャットサービス
        ↓
    Botインターフェース
        ↓
  共存型マイクロSNS
```

### 基本コンセプト

- 大手サービスのアカウントやアプリをそのまま利用する
- Botを共通インターフェースとして使う
- 文章・写真・タイムラインなどのSNS機能を追加する
- 小規模な地域、学校、家族、サークル、趣味の集まりで使う
- 設定ファイルによって利用サービスと機能を切り替える
- 投稿一覧では投稿者名やAさん・Bさんのような表示を行わず、投稿内容を中心に表示する
- ユーザーIDは内部管理にのみ使用し、他の利用者へ公開しない

### 仮称

正式名称は未決定だが、現在の候補は以下とする。

| 名称 | 意味 |
| `Micro Social Mesh` | 複数の入口をつなぐSNSを表す名前 |

現時点では、説明用の名称として「共存型マイクロSNS」を使用する。

## 目的

現行実装ではLINEを投稿システムの入口として利用する。Telegram、Discord、Zulipなどへの対応は、将来アダプターを追加できるよう境界だけを設計する。
サービスごとにSNSを作り直すのではなく、共通のユーザー管理・投稿保存処理へ接続する。

## 全体像

```text
ユーザー
  ↓
LINE / Telegram / Discord / Zulip
  ↓ サービス別アダプター
共通Botインターフェース
  ↓
ユーザー管理・投稿保存・タイムライン
  ↓
SQLite / 将来はPostgreSQLや外部ストレージ
```

## ディレクトリ構成

```text
my_first_bot/                  # リポジトリルート（言語非依存）
├── docs/                      # 仕様・設計・調査資料（全言語共通）
├── formal/                    # Lean 4形式証明（全言語共通）
├── python/                    # Python実装
│   ├── core/                  #   プラットフォーム非依存の共通処理
│   │   ├── models.py          #     データ型（Pydantic = OpenAPI準拠）
│   │   ├── database.py        #     DB操作（SQLite）
│   │   ├── engine.py          #     固定フロー（State → Action列）
│   │   └── config.py          #     設定読み込み
│   ├── platforms/             #   サービス別アダプター（順次追加）
│   ├── tests/                 #   テスト
│   │   ├── test_core_engine.py    # engineのテスト（DB不要）
│   │   ├── test_core_database.py  # databaseのテスト（一時SQLite）
│   │   ├── test_core_models.py    # データ型テスト（OV検証）
│   │   └── test_app.py            # 統合テスト
│   ├── app.py                 #   起動エントリポイント
│   ├── config.json            #   Python用実行時設定
│   └── requirements.txt       #   Python依存パッケージ
├── node/                      # (将来) Node.js実装
├── rust/                      # (将来) Rust実装
├── config.example.json        # 全言語共通の設定例
├── .env.example               # 環境変数テンプレート
├── README.md
└── .gitignore
```

## モジュール責務

### python/core/models.py — 共通データ型

Pydantic v2 で実装し、`docs/openapi.yaml` のスキーマと一致させる。
プラットフォームアダプターと共通処理の境界をこの型で固定する。

```python
class InboundEvent(BaseModel):
    platform: str
    user_id: str
    content_type: Literal["text", "image", "audio", "video", "file"]
    text: str | None = None
    media_url: str | None = None

class OutboundReply(BaseModel):
    messages: list[OutboundMessage]
```

### python/core/database.py — DB操作

| 関数 | 役割 |
|---|---|
| `init_db()` | テーブル作成・マイグレーション |
| `get_user(platform, user_id)` | ユーザー取得、なければNone |
| `create_user(platform, user_id)` | 新規ユーザー作成 |
| `has_posts(user_id)` | 公開済み投稿の有無 |
| `save_post(user_id, type, text, ...)` | 投稿保存、IDを返す |
| `get_recent_posts(user_id, limit)` | 最近の投稿一覧 |

SQLite直操作。将来のストレージ変更はこの層だけ書き換える。

### python/core/engine.py — 固定フロー

Lean 4の `step` 関数に対応する2つの純粋関数で構成する。

| 関数 | 役割 | Lean対応 |
|---|---|---|
| `decide_actions(is_first, event)` | Action列を返す | `step(state, input) → (state, actions)` |
| `build_reply(actions, recent_posts)` | Actionから返信を組み立て | 実装側の整形 |

プラットフォームAPI・ネットワーク・ファイルI/Oに依存しない。
`formal/FixedFlow.lean` の定理がそのままPython版のテスト項目になる。

### python/core/config.py — 設定

`config.json` の読み込み。バリデーションは最小限に保つ。

## OV（OpenAPI Validation）層

アダプターとcoreの境界で、OpenAPIスキーマに基づくバリデーションを行う。

```text
Platform Event
  ↓ Adapter が共通形式に変換
  ↓ OV: Pydanticモデルで型検証（core/models.py）
  ↓
core/engine.py（純粋ロジック）
  ↓
OutboundReply（Pydanticモデル）
  ↓ OV: 出力も型保証
  ↓ Adapter がプラットフォーム形式に変換
  ↓
Platform Reply
```

- `core/models.py` はPydantic v2で実装し、`docs/openapi.yaml` のスキーマと一致させる
- 入力は `InboundEvent`、出力は `OutboundReply` で型が保証される
- 不正な形式はアダプター境界でValidationErrorとして捕捉する
- 参照OSS: **FastAPI + Pydantic**（リクエスト/レスポンスの型保証パターン）

## テスト戦略 — ビューアイソレーション

プラットフォームアダプター（view層）と共通処理（core）を分離し、**coreは外部依存なしでテストする**。

| テスト | 分離方法 | 依存 |
|---|---|---|
| `test_core_engine.py` | DB呼び出しをモック/Memoryで置換 | なし |
| `test_core_database.py` | 一時SQLite (`tempfile`) | sqlite3のみ |
| `test_core_models.py` | 純粋なデータ型テスト | なし |
| `test_app.py` | Flaskテストクライアント | Flask, sqlite3 |
| 将来: `test_line_adapter.py` | LINE SDKをモック | 要 mock |

- どのテストも `.env` ・実トークン・実ネットワークを必要としない
- `python -m unittest discover -s tests -v` 一発で全テスト実行
- Leanの定理 → engineのテスト項目、として追跡可能にする

## 共通インターフェース

各アダプターは、受信したサービス固有のメッセージを共通形式へ変換する。

```json
{
  "platform": "telegram",
  "user_id": "platform-user-id",
  "type": "text",
  "text": "投稿内容",
  "media": null
}
```

共通処理は、入力がLINE由来かTelegram由来かを意識せずに投稿を保存する。返信時だけ、各サービスのメッセージ形式へ変換する。

返信形式は入力コンテンツに合わせる。写真の投稿には写真、動画の投稿には動画というように同種の形式を優先し、対応できない場合だけテキストへフォールバックする。

## 設定による切り替え

```json
{
  "features": {
    "text_post": true,
    "image_post": true
  },
  "media": {
    "enabled_types": ["image", "audio", "video", "file"]
  }
}
```

トークンや秘密鍵は設定ファイルへ書かず、環境変数で管理する。設定ファイルは「どのサービスを有効にするか」「どの機能を提供するか」を指定するために使う。

## 各サービスで異なる部分

- ユーザーIDの形式
- Webhookやイベントの受信方法
- 画像・ファイルの取得方法
- 返信メッセージの上限
- ボタン、スタンプ、リアクションなどの機能
- Botに必要な権限

### コンテンツ対応の考え方

共通SNSは複数の投稿種別を定義し、プラットフォームごとに対応可能な種別をアダプターで宣言する。

| 投稿種別 | LINE | Telegram | Discord | Zulip |
| --- | --- | --- | --- | --- |
| 文章 | 対応 | 対応 | 対応 | 対応 |
| 写真 | 対応 | 対応 | 対応 | 要確認 |
| 音声 | 対応 | 対応 | 対応 | 要確認 |
| 動画 | 対応 | 対応 | 対応 | 要確認 |
| ファイル | 対応 | 対応 | 対応 | 対応 |
この表は実装時に各公式APIで確認する。対応しない種別があっても、文章投稿やタイムラインなど共通部分は利用できる。

これらはアダプター内で吸収し、共通処理へサービス固有の仕様を持ち込まない。

## 実装順序

1. **python/core/ の作成とテスト**（完了）
   - `python/core/models.py` — データ型（Pydantic = OpenAPI準拠）
   - `python/core/engine.py` — 固定フローのAction列を返す（純粋関数）
   - `python/core/database.py` — DB操作（SQLite直操作）
   - `python/core/config.py` — 設定読み込み
   - 対応するテストを先に書き、ビューアイソレーションで実行
   - テスト項目は `formal/FixedFlow.lean` の定理と対応させる

2. **app.py を core/ 呼び出しに置き換え**（未着手）
   - app.pyはFlask + LINE Webhookだけに薄くする
   - メッセージハンドラは `core/engine.py` と `core/database.py` を呼ぶ形に変更
   - 既存のテスト46件が全て通ることを確認

3. **LINEアダプターを python/platforms/line/ へ分離**（未着手）
   - LINE固有の処理（署名検証、メディア取得、返信形式変換）を移す
   - `python/platforms/base.py` にアダプター契約を定義

4. **Telegramアダプター追加**（未着手）
   - 共通インターフェースが正しく機能することを確認
   - Telegram用のテストを追加

5. **Discord、Zulip、その他**（未着手）
   - 調査結果（docs/platforms/）を基に優先順位を決定
   - 追加はアダプターだけ、python/core/は変更しない

最初から全サービスを同時に実装せず、共通インターフェースを先に固定する。
各ステップでテストを先に書き、コードはテストを通すために書く。

## 将来機能を受け入れる境界

翻訳と広告は現行MVPおよび直近の実装対象外とする。将来再検討する場合は、固定フローを変更しない拡張レイヤーとして設計する。

```text
Platform Adapter
  → Normalize Event
  → Optional Extensions
  → Core Save
  → Recent Posts
  → Optional Reply Extensions
  → Platform Reply
```

MVPではOptional Extensionsを無効にする。現在のユーザー体験は「送るだけ」に保つ。

## ブラックボックスとしての拡張

翻訳と広告は、共通イベントを受け取り、共通形式の結果を返すブラックボックスとして接続する。

```text
共通イベント
  ↓
┌────────────────────┐
│ Extension           │
│ 翻訳 / 広告          │
└────────────────────┘
  ↓
共通イベント・返信要素
```

本体は拡張の内部を参照しない。拡張を追加・交換・削除しても、MVPの保存と返信は成立するようにする。

### 拡張の接続位置

- 受信後：翻訳、画像変換、モデレーション
- 保存後：分析、分類、広告候補の作成
- 返信前：翻訳、広告の追加、表示形式の変換

将来機能はこの接続位置にプラグインとして追加する。プラットフォームアダプターと同じく、共通契約を守る限り実装言語や提供元を限定しない。

## ユーザー単位の送信時変換

投稿は一つの共通データとして保存し、取得した最新投稿を返信する直前に、返信先ユーザーの設定に応じて変換する。

```text
投稿保存（共通）
      ↓
最新投稿取得（共通）
      ↓
ユーザー設定を適用
      ↓
翻訳・広告・画像変換など
      ↓
返信
```

これにより、同じ投稿でもユーザーごとに異なる表示ができる。投稿データそのものを書き換えないため、拡張機能を追加しても本体の保存処理は変更しない。

## 参照OSSパターン

| プロジェクト | 参考にする点 |
|---|---|
| **FastAPI** | Pydantic v2によるリクエスト/レスポンスの型保証と自動バリデーション。`core/models.py` のOV層で同じパターンを採用。 |
| **Flask** | シンプルな起動エントリポイント。`app.py` はこの程度の薄さに保つ。 |
| **SQLAlchemy** (設計のみ) | RepositoryパターンによるDBアクセスの抽象化。`core/database.py` は当面SQLite直操作だが、将来このパターンで差し替え可能にする。 |
| **CPython 標準庫** | `unittest` + `tempfile` で外部依存ゼロのテスト。サードパーティmockに頼らない方法を優先。 |
