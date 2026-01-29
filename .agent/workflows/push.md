---
description: Botの自動更新(GitHub Actions)と自身の変更を同期して安全にプッシュします
---

# /push ワークフロー: 安全な同期プッシュ

このプロジェクトは GitHub Actions によって1時間おきに自動更新されます。自身の変更を安全に公開するための手順です。

// turbo-all
1. 最新のリモート変更(Botの更新)を確認し、自身の変更をその上に乗せます
   `git pull --rebase origin main`

2. 同期した最新の状態を GitHub にプッシュします
   `git push origin main`

3. サイトのデプロイ状況を確認するためのURLを提示します
   URL: https://github.com/TadFuji/AI_TOOL_NEWS/actions

4. デプロイ完了後、公開サイトの状態を確認することを提案します
   URL: https://tadfuji.github.io/AI_TOOL_NEWS/
