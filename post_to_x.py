import os
import json
import glob
import re
import datetime
import tweepy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
POSTED_HISTORY_FILE = "posted_history.json"
REPORTS_DIR = "reports"

# X API Credentials (from Environment Variables)
CONSUMER_KEY = os.environ.get("X_CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("X_CONSUMER_SECRET")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET")

def load_history():
    """Loads the history of posted news URLs/IDs."""
    if os.path.exists(POSTED_HISTORY_FILE):
        try:
            with open(POSTED_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_history(history):
    """Saves the updated history."""
    with open(POSTED_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_twitter_client():
    """Initializes and returns the Tweepy Client for X API v2."""
    if not all([CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        print("Warning: Missing X API credentials. Skipping posting.")
        return None

    try:
        client = tweepy.Client(
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET
        )
        return client
    except Exception as e:
        print(f"Error initializing X Client: {e}")
        return None

def parse_report_file(filepath):
    """Parses a JSON report file to extract news items."""
    items = []
    
    if filepath.endswith('.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            tool_name = data.get('tool', 'Unknown')
            category = data.get('category', 'AI News')
            url = data.get('url', '')
            summary_raw = data.get('summary', '')

            # Extract clean summary from Gemini's markdown output if present
            summary = summary_raw
            if "**Summary**:" in summary_raw:
                s_match = re.search(r'\*\*Summary\*\*:\s*(.*)', summary_raw, re.DOTALL)
                if s_match:
                    summary = s_match.group(1).strip()
            
            # Final cleanup
            summary = summary.replace("**", "").replace("- ", "").strip()
            # Remove any trailing "URL: ..." or "Date: ..." if they leaked in
            summary = re.split(r'\n(URL|Date|Time):', summary)[0].strip()

            if "No significant news found" in summary:
                return []

            if len(summary) > 5 and url.startswith("http"):
                items.append({
                    "tool": tool_name,
                    "category": category,
                    "summary": summary,
                    "url": url,
                    "id": url
                })
        except Exception as e:
            print(f"Error parsing JSON {filepath}: {e}")
        return items

    # Note: Legacy Markdown format is no longer supported.
    # All reports are now stored as JSON (since 2026-01-29 JSON Pivot).
    return items

def post_item_to_x(item, client=None):
    """Posts a single news item to X."""
    if not client:
        client = get_twitter_client()
    if not client:
        return False

    history = load_history()
    if item['id'] in history:
        return False

    # Construct Tweet
    tweet_text = f"📢 {item['tool']} Update!\n\n{item['summary']}\n\n{item['url']}\n#AI #{item['category'].replace(' ', '')}"

    try:
        response = client.create_tweet(text=tweet_text)
        print(f"  -> Posted to X! Tweet ID: {response.data['id']}")
        
        history.append(item['id'])
        save_history(history)
        return True
    except Exception as e:
        print(f"  -> Failed to post to X: {e}")
        return False

def main():
    print("=== X Auto-Post Start ===")
    
    client = get_twitter_client()
    if not client:
        print("Skipping X posting due to missing credentials.")
        return

    history = load_history()
    print(f"Loaded {len(history)} previously posted items.")
    
    JST = datetime.timezone(datetime.timedelta(hours=9))
    today_str = datetime.datetime.now(JST).strftime("%Y-%m-%d")
    yesterday_str = (datetime.datetime.now(JST) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    target_dirs = [today_str, yesterday_str]
    
    all_reports = []
    for d in target_dirs:
        day_path = os.path.join(REPORTS_DIR, d)
        if os.path.exists(day_path):
            all_reports.extend(glob.glob(os.path.join(day_path, "*.json")))

    new_items_count = 0
    
    for report_path in all_reports:
        items = parse_report_file(report_path)
        for item in items:
            if post_item_to_x(item, client):
                new_items_count += 1
                
    if new_items_count == 0:
        print("No new items to post.")
    
    print("=== X Auto-Post Complete ===")

if __name__ == "__main__":
    main()
