@echo off
echo ============================================
echo  WARNING: AI TOOL NEWS は運用停止中です
echo  (2026-02-17〜)
echo  本当に実行しますか？
echo ============================================
set /p CONFIRM="続行する場合は Y を入力: "
if /i not "%CONFIRM%"=="Y" (
    echo キャンセルしました。
    pause
    exit /b
)
echo AI TOOL NEWS 更新プロセスを開始します...
python collect_ai_news.py
python build_site.py
git add .
git commit -m "ニュース自動更新 (%date% %time%)"
git push
echo すべての作業が完了しました。
pause
