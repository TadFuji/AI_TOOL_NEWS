@echo off
cd /d %~dp0
echo =================================================== >> update_log.txt
echo [%date% %time%] Starting Scheduled Auto-Update >> update_log.txt

echo 1. Running News Collection...
python collect_ai_news.py
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: News collection failed. >> update_log.txt
    exit /b %errorlevel%
)

echo 2. Building Website...
python build_site.py
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Site build failed. >> update_log.txt
    exit /b %errorlevel%
)

echo 3. Deploying to GitHub...
git add .
git commit -m "Auto-update: %date% %time%"
git push origin main
if %errorlevel% neq 0 (
    echo [%date% %time%] NOTICE: Git push failed or nothing to push. >> update_log.txt
) else (
    echo [%date% %time%] SUCCESS: deployed to GitHub. >> update_log.txt
)

echo =================================================== >> update_log.txt
