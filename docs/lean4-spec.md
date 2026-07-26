# Lean 4による本体仕様の検証

## 目的

Lean 4をBot本体の実装言語にはせず、確定した固定フローが仕様どおりであることを検証するために使う。

## 検証対象

```text
最初の対応投稿（文章・写真・音声・動画・ファイル）
  → 保存し、使い方を返信する
次の対応投稿（文章・写真・音声・動画・ファイル）
  → 保存し、最近の投稿を返信する
```

## 状態

```lean
inductive State
  | firstPost
  | readyForPost
deriving Repr, DecidableEq
```

## 入力

```lean
inductive Input
  | text (value : String)
  | image (mediaId : String)
  | audio (mediaId : String)
  | video (mediaId : String)
  | file (mediaId : String)
deriving Repr
```

## Botの結果

```lean
inductive Action
  | showUsage
  | saveText (value : String)
  | saveImage (mediaId : String)
  | saveAudio (mediaId : String)
  | saveVideo (mediaId : String)
  | saveFile (mediaId : String)
  | replyRecentPosts
deriving Repr
```

## 固定遷移

```lean
def step : State → Input → State × List Action
  | .firstPost, .text value =>
      (.readyForPost, [.saveText value, .showUsage])
  | .firstPost, .image mediaId =>
      (.readyForPost, [.saveImage mediaId, .showUsage])
  | .firstPost, .audio mediaId =>
      (.readyForPost, [.saveAudio mediaId, .showUsage])
  | .firstPost, .video mediaId =>
      (.readyForPost, [.saveVideo mediaId, .showUsage])
  | .firstPost, .file mediaId =>
      (.readyForPost, [.saveFile mediaId, .showUsage])
  | .readyForPost, .text value =>
      (.readyForPost, [.saveText value, .replyRecentPosts])
  | .readyForPost, .image mediaId =>
      (.readyForPost, [.saveImage mediaId, .replyRecentPosts])
  | .readyForPost, .audio mediaId =>
      (.readyForPost, [.saveAudio mediaId, .replyRecentPosts])
  | .readyForPost, .video mediaId =>
      (.readyForPost, [.saveVideo mediaId, .replyRecentPosts])
  | .readyForPost, .file mediaId =>
      (.readyForPost, [.saveFile mediaId, .replyRecentPosts])
```

## 検証したい性質

1. 最初の文章は保存され、`showUsage`が発生する。
2. 最初の写真は保存され、`showUsage`が発生する。
3. 最初の音声は保存され、`showUsage`が発生する。
4. 最初の動画は保存され、`showUsage`が発生する。
5. 最初のファイルは保存され、`showUsage`が発生する。
6. 2回目以降の文章は保存される。
7. 2回目以降の写真は保存される。
8. 2回目以降の音声は保存される。
9. 2回目以降の動画は保存される。
10. 2回目以降のファイルは保存される。
11. 2回目以降の保存後は最近の投稿を返信する。
12. キーワード・コマンドによる分岐が存在しない。
13. Botから先にPush通知する遷移が存在しない。

現在の `FixedFlow.lean` は性質1・2・6・7・11・12・13を証明済み。
性質3〜5・8〜10（音声・動画・ファイル）は型定義と遷移関数は実装済み、定理は未証明。

## 実装との関係

```text
Lean 4
  ↓ 固定フローの検証
OpenAPI / JSON Schema
  ↓ 共通インターフェース
PHP / Python / Node.jsなど
  ↓ 各サービスのアダプター
LINE / Telegram / Discord / その他
```

Lean 4のモデルと実装が同じ入力に対して同じ動作をすることを、各言語版のテストで確認する。

Python版は `tests/test_core_engine.py` が対応する。

- `decide_actions(is_first_post=True, text)` = Leanの `step(.firstPost, .text value)`
- `decide_actions(is_first_post=True, image)` = Leanの `step(.firstPost, .image mediaId)`
- `decide_actions(is_first_post=True, audio/video/file)` = Leanの同種（`SAVE_MEDIA` に統合）
- `decide_actions(is_first_post=False, text)` = Leanの `step(.readyForPost, .text value)`
- `decide_actions(is_first_post=False, image/audio/video/file)` = Leanの同種
- `test_no_keyword_branching` = Leanの性質12
- `test_no_push_action_type_exists` = Leanの性質13

参考: Python実装はメディア種別を `SAVE_MEDIA` 1つのActionに統合しているが、これは実装上の省略であり、全5種に対して同じフロー（保存+返信）が実行されることはLeanのモデルと一致する。

## 対象外

- Lean 4からBotサーバーを直接運用すること
- Lean 4から各プラットフォームAPIを直接呼び出すこと
- 翻訳・広告・分析などの将来機能の検証

これらは本体仕様が変更された場合に、別の検証対象として追加する。
