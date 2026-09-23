# TESTEA Marketing

個別指導塾TESTEAのマーケティング施策を一元管理するリポジトリです。
Webサイト、コンテンツ企画、効果測定を横断的に扱うモノレポ構成にしています。

## ディレクトリ構成

| ディレクトリ | 役割 |
| --- | --- |
| [`docs/`](docs/) | ブランドガイドライン・マーケティング戦略ドキュメント |
| [`site/`](site/) | LP・コーポレートサイトのコード |
| [`content/`](content/) | SNS・ブログ・広告のコンテンツ企画とカレンダー |
| [`analytics/`](analytics/) | 効果測定レポートと集計スクリプト |
| [`.claude/skills/`](.claude/skills/) | Claude Codeが使うマーケティング特化スキル集 |

## Claude Codeマーケティングスキル

[coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)(MIT License)のスキル一式を `.claude/skills/` に取り込んでいます。Claude Codeでこのリポジトリを開くと、CRO・コピーライティング・SEO・広告・メール・SNSなど50種類のマーケティングタスク別スキルが自動で使えるようになります。

- 例: 「このLPのCVRを改善したい」→ `cro` スキルが使われる
- 例: 「ホームページのコピーを書いて」→ `copywriting` スキルが使われる
- 直接呼び出す場合は `/cro`, `/copywriting`, `/seo-audit` のように使用
- 各スキルの一覧・詳細は本家の[README](https://github.com/coreyhaines31/marketingskills#available-skills)を参照

### 最初にやること

`product-marketing` スキルを使って `.agents/product-marketing.md` を作成すると、塾の商品概要・ターゲット・強み等の共通コンテキストが他の全スキルから自動参照されます。`docs/brand-guideline.md` `docs/strategy.md` と役割は近いですが、こちらはスキルが直接読み込む正式なコンテキストファイルなので、内容が固まったら反映してください。

最新版への更新は本家リポジトリの `skills/` を再取得し、`.claude/skills/` を上書きしてください。

## 運用の考え方

- 施策領域ごとにディレクトリを分け、各ディレクトリのREADMEに詳細ルールを記載します。
- 特定領域(例: `site/`)の規模が大きくなった場合は、その時点で別リポジトリへの切り出しを検討します。
- ブランド関連の一次情報は `docs/brand-guideline.md` に集約し、各施策から参照します。

## 今後の進め方

各ディレクトリはまず骨組みのみ作成した状態です。以下のような単位で少しずつ中身を追加していく想定です。

1. `docs/` にブランド情報・戦略の内容を埋める
2. `content/` に直近の投稿・記事・広告の企画を追加する
3. `site/` に実際のLPコードを構築する(技術選定は着手時に相談)
4. `analytics/` に効果測定の指標定義とレポートを追加する
