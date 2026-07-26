# User Flow

## 正本

この資料は [core-spec.md](core-spec.md) の固定フローを図で示す。

## 固定フロー

```mermaid
flowchart TD
    A[最初の投稿] --> B[投稿として保存]
    B --> C[使い方を返信]
    C --> D[次の投稿]
    D --> E[投稿として保存]
    E --> F[最近の投稿を取得]
    F --> G[投稿内容だけを返信]
    G --> D
```

## 最初の投稿

```mermaid
sequenceDiagram
    participant U as User
    participant P as Platform
    participant B as Bot
    participant DB as Database

    U->>P: 最初の投稿を送る
    P->>B: 入力イベントを渡す
    B->>DB: 投稿を保存
    B-->>P: 使い方を返信
    P-->>U: 使い方を表示
    Note over B,DB: ユーザー情報の登録は内部処理として行う
```

## 2回目以降の入力

```mermaid
sequenceDiagram
    participant U as User
    participant P as Platform
    participant B as Bot
    participant DB as Database

    U->>P: 対応している投稿を送る
    P->>B: 入力イベントを渡す
    B->>DB: 投稿を保存
    B->>DB: 最近の投稿を取得
    DB-->>B: 投稿内容の一覧
    B-->>P: 保存結果と最近の投稿を返信
    P-->>U: 投稿内容だけを表示
```

## 入力と動作

| 入力 | 動作 |
| --- | --- |
| 最初の対応投稿（文章・写真・音声・動画・ファイル） | 保存し、使い方を返信 |
| 2回目以降の対応投稿（文章・写真・音声・動画・ファイル） | 保存し、最近の投稿を返信 |

返信の形式は、MVPではテキスト形式を基本とする。入力コンテンツに合わせた形式での返信（写真には写真、動画には動画）は将来対応する。

## 重要な制約

- ユーザー登録操作を要求しない
- ボタンやリッチメニューを必須にしない
- Botから先にPush通知しない
- 投稿者名やユーザーIDを表示しない
- 検索、編集、コメント、リアクションはMVPに含めない
