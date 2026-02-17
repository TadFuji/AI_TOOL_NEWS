# AI TOOL NEWS 🚀
**AIツールの最新動向を自動収集し、スタイリッシュに表示するニュースサイト**

> ⚠️ **運用停止中 (2026-02-17〜)**
> 現在、自動ニュース収集・投稿の運用を一時停止しています。
> コード・データ・レポートはすべて保持されており、再開可能な状態です。
> 詳細は本ドキュメント末尾の「運用ログ」セクションを参照してください。

[![公開サイト](https://img.shields.io/badge/Live-Demo-00f2ff?style=for-the-badge&logo=github&logoColor=white)](https://TadFuji.github.io/AI_TOOL_NEWS/)
[![ライセンス: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Powered by Grok](https://img.shields.io/badge/Powered%20by-xAI%20Grok-white?style=for-the-badge&logo=x)](https://x.ai/)

AI TOOL NEWSは、主要なAIツールや企業の公式X（旧Twitter）アカウントを常時監視し、最先端LLM（xAI Grok / Google Gemini）を用いて重要なアップデートのみを抽出、美しくモダンなウェブサイトとして自動公開するシステムです。

🔗 **Webサイトを見る:** [https://TadFuji.github.io/AI_TOOL_NEWS/](https://TadFuji.github.io/AI_TOOL_NEWS/)

---

## ✨ 主な特徴

- **自動収集**: OpenAI, Google DeepMind, Anthropicなど、30以上の主要アカウントを監視。
- **Structured Data Pivot**: 収集データはJSON形式で保存され、高いデータ整合性と高速なビルドを実現。
- **スマートフィルタリング**: 高速な **xAI grok-4-1-fast-non-reasoning** および **Google Gemini 3 Flash Preview** を使用してツイートを分析。「新機能」「モデル更新」など、価値のある情報のみを厳選。
- **モダンなデザイン**: 最新のGlassmorphism UIを採用。美しく、かつ読みやすいインターフェース。
- **サーバーレス運用**: GitHub Actionsを活用し、データベース不要で静的サイトを生成。

## 🛠️ 運用・使い方

### 1-Click 更新（推奨）
プロジェクト直下にある `update_news.bat` をダブルクリックするだけで、ニュースの収集からサイト更新、公開（GitHubへのプッシュ）までが完了します。

### 手動での更新（エンジニア向け）
1. **ニュースを収集する**
   ```bash
   python collect_ai_news.py
   ```
2. **サイトをビルドする**
   ```bash
   python build_site.py
   ```
3. **公開する**
   ```bash
   git add .
   git commit -m "ニュース更新"
   git push
   ```

## 🏗️ システム構成と保守

### 重要な注意点（トラブルシューティング）
- **レポートの蓄積**: `reports/` ディレクトリには日別のJSONレポートが格納されます。Gitの管理対象ですので、削除しないでください。
- **APIキーの設定**: `.env` ファイルに `XAI_API_KEY` と `GOOGLE_API_KEY` を正しく設定してください。
- **データ整合性**: 2026年1月29日にデータフォーマットをJSONに完全移行し、不要なレガシーファイルをクリーンアップ済みです。

### 対象の追加・変更
監視対象は `targets.json` で管理されています。アカウントを追加したい場合は、このファイルを編集してください。

### LLMモデルの固定と変更禁止ポリシー
本プロジェクトでは、パフォーマンス、コスト、および出力の安定性の観点から、以下のモデルを意図的に選択しています。**AIエージェントによる自動的なモデル更新や変更は、藤川さんの明示的な合意がない限り、厳格に禁止されています。**

- **収集用 (xAI)**: `grok-4-1-fast-non-reasoning`
- **フィルタリング・要約用 (Google)**: `gemini-3-flash-preview`

これらのモデル名をコード上から発見した場合、いかなる場合も（「最新モデルへの更新」目的であっても）変更しないでください。

## 🚧 プロジェクトの境界線
このプロジェクトは「**X（Twitter）からのリアルタイムなツール情報収集**」に特化しています。

---
## 🤖 AI Agent Instructions

> ⚠️ 現在このプロジェクトは **運用停止中** です。自動更新は行われていません。

AIエージェントがプログラムの修正やUIの変更をプッシュする際は、以下のルールを厳守してください。

1. **プッシュ前の同期**: 自身の変更をプッシュする前に、必ず `git pull --rebase origin main` を実行してGitHub側の最新状態を取り込んでください。
2. **ワークフローの活用**: `.agent/workflows/push.md` に定義された `/push` コマンドを使用することで、安全に同期とデプロイ確認を行うことができます。

---
## 📝 運用ログ

| 日付 | 内容 |
|------|------|
| 2026-02-17 | **運用一時停止**。GitHub Actionsの自動トリガー（`push` / `schedule`）をコメントアウト。手動実行（`workflow_dispatch`）のみ残存。コード・データ・レポートはすべて保持。 |

### 🔄 運用再開の手順

運用を再開（リベンジ）する場合は、以下の手順で復帰できます：

1. `.github/workflows/active_news_bot.yml` を開く
2. `# SUSPENDED:` とマークされたコメントを解除し、`push` と `schedule` トリガーを復活させる
3. `.env` のAPIキー（`XAI_API_KEY`, `GOOGLE_API_KEY`, X API関連）が有効であることを確認する
4. GitHub Secretsの各キーも有効期限切れがないか確認する
5. `workflow_dispatch` で手動実行し、正常動作を確認してからトリガーを有効化する
6. 本READMEの運用停止バナーを削除し、運用ログに再開日を記録する

---
*Created by [TadFuji](https://github.com/TadFuji)*
