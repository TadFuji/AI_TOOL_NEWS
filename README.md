# AI TOOL NEWS 🚀
**AIツールの最新動向を自動収集し、スタイリッシュに表示するニュースサイト**

[![公開サイト](https://img.shields.io/badge/Live-Demo-00f2ff?style=for-the-badge&logo=github&logoColor=white)](https://TadFuji.github.io/AI_TOOL_NEWS/)
[![ライセンス: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Powered by Grok](https://img.shields.io/badge/Powered%20by-xAI%20Grok-white?style=for-the-badge&logo=x)](https://x.ai/)

AI TOOL NEWSは、主要なAIツールや企業の公式X（旧Twitter）アカウントを常時監視し、最先端LLM（xAI Grok / Google Gemini）を用いて重要なアップデートのみを抽出、美しくモダンなウェブサイトとして自動公開するシステムです。

🔗 **Webサイトを見る:** [https://TadFuji.github.io/AI_TOOL_NEWS/](https://TadFuji.github.io/AI_TOOL_NEWS/)

---

## ✨ 主な特徴

- **自動収集**: OpenAI, Google DeepMind, Anthropicなど、30以上の主要アカウントを監視。
- **Structured Data Pivot**: 収集データはJSON形式で保存され、高いデータ整合性と高速なビルドを実現。
- **スマートフィルタリング**: 高速な **xAI grok-4-1-fast** および **Google Gemini** を使用してツイートを分析。「新機能」「モデル更新」など、価値のある情報のみを厳選。
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

## 🚧 プロジェクトの境界線
このプロジェクトは「**X（Twitter）からのリアルタイムなツール情報収集**」に特化しています。

---
*Created by [TadFuji](https://github.com/TadFuji)*
