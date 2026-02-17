---
description: 変更を安全にプッシュします（運用停止中のため自動更新はありません）
---

# /push ワークフロー: 安全な同期プッシュ

このプロジェクトは **現在運用停止中** です（2026-02-17〜）。自動更新はありませんが、手動変更をプッシュする際は以下の手順に従ってください。

// turbo-all
1. 最新のリモート変更(Botの更新)を確認し、自身の変更をその上に乗せます
   `git pull --rebase origin main`

2. 同期した最新の状態を GitHub にプッシュします
   `git push origin main`

3. サイトのデプロイ状況を確認するためのURLを提示します
   URL: https://github.com/TadFuji/AI_TOOL_NEWS/actions

4. デプロイ完了後、公開サイトの状態を確認することを提案します
   URL: https://tadfuji.github.io/AI_TOOL_NEWS/
