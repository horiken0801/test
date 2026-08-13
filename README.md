# X / Threads 自動運用ボット

X（旧Twitter）とThreadsをそれぞれ自動運用するためのツールキットです。GitHub Actionsの定期実行で、次の3つのサイクルを回します。

1. **コンテンツ自動生成**（週次）: 戦略ファイル（`data/strategy.json`）のトピック・トーンに沿って投稿文をAIで生成し、`content_queue/queue.json` に予約投稿として積む
2. **予約投稿・自動投稿**（毎時）: キューの中で投稿時刻が来たものをX / Threadsそれぞれに自動投稿する
3. **インサイト分析**（週次）: 直近の投稿の反応（いいね・返信・リポスト等）を取得し、傾向から仮説を立てて `data/strategy.json` にフィードバックする（例: エンゲージメントが高い時間帯を投稿枠に追加）

3が1にフィードバックすることで、運用を続けるほど戦略ファイルが実績に基づいて更新されていきます。

## 構成

```
socialbot/                 # コアロジック（Pythonパッケージ）
  config.py                 # 環境変数・パス設定
  queue.py                  # 投稿キューの読み書き
  strategy.py                # 戦略ファイル（トーン/トピック/投稿時間/仮説）の読み書き
  content_generator.py       # 投稿文の自動生成（Claude API、未設定時はテンプレート）
  insights_analyzer.py       # 投稿実績の分析と戦略ファイルへの反映
  platforms/
    x.py                     # X API v2 クライアント（投稿・自分の投稿の指標取得）
    threads.py                # Threads API クライアント（投稿・インサイト取得）
scripts/
  generate_content.py        # コンテンツ生成CLI
  publish_posts.py           # 予約投稿の実行CLI
  analyze_insights.py        # インサイト分析CLI
data/
  strategy.json               # 現在の運用戦略（AIによる自動更新対象）
  insights_history/           # 分析結果のスナップショット（実行ごとに1ファイル）
content_queue/
  queue.json                  # 投稿キュー（pending/posted/failed/skipped）
.github/workflows/            # GitHub Actions定期実行の定義
tests/                        # pytestによるユニットテスト（ネットワーク非依存）
```

## 事前準備: APIキーの取得

まだAPIキーを取得していない場合、以下が必要です。

### X (Twitter) API

1. https://developer.x.com/en/portal/dashboard で開発者アカウントを作成し、アプリを作成
2. アプリの権限を **Read and Write** に設定（投稿するため）
3. 「Keys and tokens」から以下を発行
   - API Key / API Key Secret（Consumer Key/Secret）
   - Access Token / Access Token Secret（アプリの権限をRead and Writeにしてから発行すること）
4. 投稿頻度によっては有料プラン（Basic以上）が必要な場合があります。無料枠の投稿数上限を確認してください。

### Threads API

1. https://developers.facebook.com/ でMetaアプリを作成し、「Threads API」プロダクトを追加
2. 対象のThreadsアカウントを認可し、`threads_basic` `threads_content_publish` `threads_manage_insights` のスコープでアクセストークンを取得
3. 短期トークンを長期トークン（約60日）に交換し、`THREADS_ACCESS_TOKEN` に設定
4. トークンに紐づく `threads_user_id` を取得して `THREADS_USER_ID` に設定
5. 長期トークンは60日で失効するため、定期的な更新運用（手動 or 別途リフレッシュ処理）が必要です

### コンテンツ自動生成（任意）

`ANTHROPIC_API_KEY` を設定するとClaudeが投稿文を生成します。未設定の場合は簡易テンプレートで代替されるため、まずはキー無しで動作確認できます。

## GitHub Secretsの設定

リポジトリの Settings > Secrets and variables > Actions で以下を登録してください。

| Secret名 | 用途 |
| --- | --- |
| `X_API_KEY` / `X_API_SECRET` / `X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` | X投稿・指標取得 |
| `THREADS_ACCESS_TOKEN` / `THREADS_USER_ID` | Threads投稿・インサイト取得 |
| `ANTHROPIC_API_KEY` | コンテンツ自動生成（任意） |

`ANTHROPIC_MODEL` はSecretではなくVariables（Settings > Secrets and variables > Actions > Variables）に設定すると `generate-content.yml` から参照されます。未設定時は `claude-sonnet-5` を使用します。

## ワークフロー

すべて `workflow_dispatch` で手動実行も可能です（Actionsタブから実行）。スケジュールは各YAMLの `cron` を編集して調整してください（UTC指定）。

- `.github/workflows/generate-content.yml`: 毎週日曜21:00 JSTにX/Threads向けドラフトを生成し、`content_queue/queue.json` にコミット
- `.github/workflows/publish-posts.yml`: 毎時、投稿時刻が来たキュー項目を投稿し、ステータスをコミット
- `.github/workflows/analyze-insights.yml`: 毎週月曜22:00 JSTに実績を分析し、`data/strategy.json` を更新
- `.github/workflows/tests.yml`: push/PR時にpytestを実行

いずれもリポジトリへの書き込み用に `permissions: contents: write` と `GITHUB_TOKEN`（デフォルトで利用可能）を使い、生成物をボットコミットとしてpushします。

## コンテンツキューの運用

`content_queue/queue.json` は直接編集して手動で投稿を追加・削除・スケジュール変更しても構いません。各項目のスキーマ:

```json
{
  "id": "一意なID（自動採番）",
  "platform": "x または threads",
  "text": "投稿本文",
  "topic": "紐づくトピック名",
  "scheduled_time": "ISO8601（JST推奨）",
  "status": "pending | posted | failed | skipped",
  "post_id": "投稿後に設定されるプラットフォーム側ID",
  "error": "失敗時のエラーメッセージ"
}
```

投稿前に内容を確認したい場合は、`generate-content.yml` の実行後・`publish-posts.yml` が拾う前にPRやコミットでレビュー・修正してください。

## ローカルでの動作確認

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # 値を埋める（未設定でもテンプレート生成やテストは動く）

# ドラフト生成（.envにANTHROPIC_API_KEYがあればClaudeで生成、無ければテンプレート）
python scripts/generate_content.py --platform both --count 2

# 投稿時刻が来たものを投稿（X/Threadsの認証情報が必要）
python scripts/publish_posts.py

# 実績分析と戦略ファイルの更新（X/Threadsの認証情報が必要）
python scripts/analyze_insights.py

# ユニットテスト（ネットワーク接続不要）
pytest
```

## 注意事項

- 各プラットフォームの自動化・スパム防止ポリシーを順守してください。特に投稿頻度・同一内容の連投・大量フォロー等は規約違反になり得ます
- 投稿前レビューを挟みたい場合は `publish-posts.yml` の実行前にキューをPRでレビューするフローに変更することを推奨します
- Threadsの長期アクセストークンは約60日で失効します。失効前に更新する運用を別途用意してください
- `insights_analyzer.py` の傾向分析はエンゲージメント（いいね+返信+リポスト）の時間帯別平均という単純なヒューリスティックです。運用データが増えてきたらロジックの高度化を検討してください
