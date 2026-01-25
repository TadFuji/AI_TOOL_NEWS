import os
import sys
import glob
import json
import datetime
import requests
from datetime import timezone

# Configuration
API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-beta" # Use a capable model for writing
REPORTS_DIR = "reports"

def load_week_news():
    """Loads all news reports from the last 7 days."""
    JST = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(JST)
    
    # Schedule Check: Only run on Sunday (6) at 8 AM
    # GitHub Actions runs hourly.
    if now.weekday() != 6: # 0=Mon, ... 6=Sun
        print("🕒 Not Sunday. Skipping Weekly Report.")
        sys.exit(0)
        
    if now.hour != 8:
        print("🕒 Not 8:00 AM. Skipping Weekly Report.")
        sys.exit(0)

    print("📅 Sunday 8:00 AM detected. Starting Weekly Editor...")
    
    today = now
    
    reports = []
    
    # Scan last 7 days
    for i in range(7):
        date = today - datetime.timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        day_path = os.path.join(REPORTS_DIR, date_str)
        
        if os.path.exists(day_path):
            # Tool Reports
            for f in glob.glob(os.path.join(day_path, "*.md")):
                with open(f, 'r', encoding='utf-8') as file:
                    reports.append(file.read())
            # General News
            for f in glob.glob(os.path.join(day_path, "general_news", "*.md")):
                with open(f, 'r', encoding='utf-8') as file:
                    reports.append(file.read())
                    
    return reports

def generate_column(news_text):
    """Asks AI to write a weekly column."""
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        print("Skipping column generation: No API Key")
        return None
        
    prompt = (
        "Role: Expert AI Tech Journalist (like a mix of TechCrunch editor and a witty columnist).\n"
        "Task: Write a 'Weekly AI Trend Report' based on the provided news snippets.\n\n"
        "Content Requirements:\n"
        "1. **The Big Picture**: What was the single defining theme of this week? (e.g., 'The Week Agents Took Over' or 'Google Strikes Back').\n"
        "2. **Winner & Loser**: Pick one winner (company/tech) and one loser (stagnant player) with reasons.\n"
        "3. **Deep Dive Column**: Write a 3-paragraph opinion piece on where this is heading. Be provocative, insightful, and forward-looking. Don't just summarize.\n"
        "4. **Format**: Markdown. Make it engaging to read.\n\n"
        "Target Audience: Japanese AI Engineers and Business Leaders.\n"
        "Language: **JAPANESE (Natural, Professional, engaging)**.\n\n"
        f"News Data:\n{news_text[:50000]}..." # Truncate to avoid context limit if massive
    )

    payload = {
        "messages": [
            {"role": "system", "content": "You are a top-tier AI Journalist."},
            {"role": "user", "content": prompt}
        ],
        "model": MODEL,
        "temperature": 0.7
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"API Error: {response.text}")
            return None
    except Exception as e:
        print(f"Request Failed: {e}")
        return None

def main():
    print("=== Weekly Editor Mode Start ===")
    
    # 1. Gather Data
    news_items = load_week_news()
    if not news_items:
        print("No news found for this week.")
        return

    print(f"Analyzed {len(news_items)} reports from the last 7 days.")
    full_text = "\n---\n".join(news_items)
    
    # 2. Generate Content
    column = generate_column(full_text)
    
    if column:
        # 3. Save Report
        JST = datetime.timezone(datetime.timedelta(hours=9))
        today_str = datetime.datetime.now(JST).strftime("%Y-%m-%d")
        
        # Save as a Special Report in today's folder
        report_dir = os.path.join(REPORTS_DIR, today_str, "weekly_special")
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
            
        filename = "Weekly_Trend_Column.md"
        filepath = os.path.join(report_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# 📅 週刊AIトレンド ({today_str})\n\n")
            f.write(column)
            
        print(f"✅ Weekly Column Generated: {filepath}")
        
    else:
        print("❌ Failed to generate column.")

if __name__ == "__main__":
    main()
