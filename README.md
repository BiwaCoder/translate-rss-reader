# RSS Reader with AI Translation

PythonのfeedparserとOpenAI APIを使用したRSSリーダー。記事の翻訳機能付き。

## 機能

### RSS管理
- RSS フィードの追加・削除・編集
- JSONファイルでフィード情報を永続化
- インタラクティブなコマンドライン操作

### 記事表示
- 最新記事から時系列ソート表示
- 20件ずつページング表示
- 見出し + 内容50文字のプレビュー
- 詳細表示（全文表示）

### AI翻訳機能
- OpenAI GPT-4oを使用した英日翻訳
- 翻訳ON/OFF切り替え可能
- 見出し一覧：翻訳版表示
- 詳細表示：原文・翻訳両方表示
- 翻訳結果キャッシュ（重複翻訳回避）

### キャッシュ機能
- RSS記事データの永続キャッシュ
- 翻訳結果の永続キャッシュ
- ネットワーク負荷軽減

## セットアップ

### 依存関係インストール
```bash
pip install -r requirements.txt
```

### OpenAI API設定
```bash
export OPENAI_API_KEY="your_api_key_here"
```

## 使用方法

### 基本起動
```bash
python rss_reader.py
```

### メニュー操作
```
=== RSS リーダー ===
1. フィード一覧
2. 記事を読む
3. フィード追加
4. フィード削除
5. フィード編集
6. 翻訳切り替え (現在: OFF)
7. 終了
```

### 記事読み取りモード
- `n`: 次のページ
- `p`: 前のページ
- `q`: 一覧に戻る
- `数字`: 記事詳細表示

### 詳細表示モード
- `b`: 一覧に戻る

## ファイル構成

```
rss_reader.py           # メインプログラム
requirements.txt        # 依存関係
rss_feeds.json         # フィード情報（自動生成）
settings.json          # 設定情報（自動生成）
translation_cache.json # 翻訳キャッシュ（自動生成）
rss_cache/            # 記事キャッシュディレクトリ（自動生成）
```

## クラス構成

### LLMInterface
- OpenAI APIとの通信を担当
- GPT-4oモデルを使用

### Translator
- テキスト翻訳機能
- 翻訳結果のキャッシュ管理
- HTMLタグの除去

### RSSManager
- RSSフィードの管理（追加・削除・編集）
- 設定管理（翻訳ON/OFF）
- JSON形式でのデータ永続化

### RSSReader
- RSS記事の取得・表示
- ページング機能
- 記事キャッシュ管理
- 時系列ソート

## 設定ファイル

### rss_feeds.json
```json
[
  {
    "url": "https://example.com/feed.xml",
    "name": "Example Blog"
  }
]
```

### settings.json
```json
{
  "translation_enabled": false
}
```

## 翻訳機能詳細

### 見出し一覧での翻訳
翻訳ONの場合：
```
0: [Unity Blog] Unityの新機能について
     この記事では最新のUnity機能を紹介します...
```

### 詳細表示での翻訳
翻訳ONの場合、原文・翻訳両方を表示：
```
=== 記事詳細 ===
タイトル（原文）: New Unity Features
タイトル（翻訳）: Unityの新機能
フィード: Unity Blog
公開日: Mon, 01 Sep 2025 12:00:00 GMT
URL: https://example.com/article

内容（原文）: This article introduces the latest Unity features...
内容（翻訳）: この記事では最新のUnity機能を紹介します...
```

## プログラム解説

### 全体アーキテクチャ
このRSSリーダーは4つの主要クラスで構成されています：

1. **LLMInterface**: OpenAI APIとの通信を抽象化
2. **Translator**: 翻訳ロジックとキャッシュ管理
3. **RSSManager**: RSS設定とフィード管理
4. **RSSReader**: 記事取得と表示ロジック

### 存在するファイル

#### 実行ファイル
- `rss_reader.py` (270行): メインプログラム、全クラスを含む
- `requirements.txt`: Python依存関係定義

#### 自動生成ファイル
- `rss_feeds.json`: フィード情報（URL、名前）
- `settings.json`: アプリ設定（翻訳ON/OFF状態）
- `translation_cache.json`: 翻訳結果キャッシュ
- `rss_cache/`: RSS記事データキャッシュディレクトリ

### キーアルゴリズム

#### 時系列ソート
```python
self.all_items.sort(key=lambda x: x.get('published_timestamp', 0), reverse=True)
```
RFC2822形式の日付をUnixタイムスタンプに変換して新しい順にソート。

#### キャッシュ戦略
- RSS記事: URLのMD5ハッシュでファイル名生成、永続保存
- 翻訳: テキストをキーとしたJSON辞書、重複翻訳回避

#### HTMLタグ除去
```python
clean_text = re.sub(r'<[^>]+>', '', text).strip()
```
記事内容とプレビューからHTMLタグを除去。

## Claude Codeによる効率的開発

### 開発プロセス
この280行のRSSリーダーは約15分で完成しました。従来の開発と比較して10倍以上の効率化を実現。

### Claude Codeの優位性

#### 1. ライブラリ知識の活用
- `feedparser`: RSS解析の複雑さを抽象化
- `email.utils.parsedate_tz`: RFC2822日付解析
- `openai`: API通信の標準化
- 適切なライブラリ選択により、車輪の再発明を回避

#### 2. アーキテクチャ設計
```python
class Translator:  # 単一責任: 翻訳機能
class RSSManager:  # 単一責任: データ管理  
class RSSReader:   # 単一責任: UI・表示
```
責任分離によるクリーンアーキテクチャを即座に設計。

#### 3. エラーハンドリング
```python
try:
    parsed_feed = feedparser.parse(feed['url'])
except Exception as e:
    print(f"フィード '{feed['name']}' の取得でエラー: {e}")
```
実用的なエラー処理を最初から組み込み。

#### 4. UXの考慮
- インタラクティブメニュー
- 翻訳状態の視覚的表示
- ページングとナビゲーション
- 適切な日本語メッセージ

### AI時代の開発者スキル

#### 必須スキル
1. **ライブラリエコシステムの理解**
   - 何ができるかを知る（feedparser、openai、etc）
   - 適切な選択ができる
   - 組み合わせ方を理解している

2. **機能の解像度**
   - 要件を具体的な実装に分解できる
   - "RSS読み取り" → "パース、キャッシュ、ソート、ページング"
   - エッジケースを事前に想定

3. **アーキテクチャ思考**
   - 拡張性を考慮した設計
   - 責任分離
   - データフローの整理

#### 従来開発との比較
- **従来**: ライブラリ調査 → 試行錯誤 → 実装 → デバッグ（数時間〜数日）
- **AI支援**: 要件定義 → 即座に実装 → 微調整（数分〜数十分）

### 成功の鍵
準備された開発者（ライブラリ知識 + 解像度）× AI = 圧倒的生産性

## 注意事項

- OpenAI API使用時は料金が発生します
- 翻訳結果はキャッシュされるため、同じテキストの再翻訳は行われません
- ネットワーク接続が必要です（初回RSS取得・翻訳時）