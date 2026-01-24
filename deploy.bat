@echo off
echo ===================================================
echo  AI TOOL NEWS - Secure Deployment Script
echo ===================================================
echo.
echo 1. Adding all files...
git add .

echo 2. Committing changes...
git commit -m "Update from local (Secure)"

echo 3. Pushing to GitHub...
git push -u origin main

echo.
echo ===================================================
echo  Deployment Complete!
echo ===================================================
pause
