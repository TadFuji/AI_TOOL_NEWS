@echo off
echo AI TOOL NEWS 更新プロセスを開始します...
python collect_ai_news.py
python build_site.py
git add .
git commit -m "ニュース自動更新 (%date% %time%)"
git push
echo 全すべての作業が完了しました。
pause
