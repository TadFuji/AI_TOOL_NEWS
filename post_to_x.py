import os
import json
import glob
import re
import datetime
import tweepy

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
    """Parses a markdown report to extract news items."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract Category
    cat_match = re.search(r'# (.*?) - Daily Report', content)
    category = cat_match.group(1) if cat_match else "AI News"

    # Split by tool sections (## ToolName)
    sections = re.split(r'^## ', content, flags=re.MULTILINE)[1:]
    
    items = []
    for section in sections:
        lines = section.strip().split('\n')
        tool_name = lines[0].strip()
        body_text = "\n".join(lines[1:]).strip()

        # Skip empty or "no news" reports
        if "Updates not found" in body_text or "No significant news" in body_text or not body_text:
            continue
        
        # Extract Summary and URL
        summary_match = re.search(r'(?:- )?\*\*Summary\*\*:? (.*)', body_text)
        url_match = re.search(r'(?:- )?\*\*URL\*\*:? (.*)', body_text)
        
        if summary_match and url_match:
            summary = summary_match.group(1).strip().replace("**", "")
            url = url_match.group(1).strip()
            
            # Simple validation to ensure we grabbed something
            if len(summary) > 5 and url.startswith("http"):
                items.append({
                    "tool": tool_name,
                    "category": category,
                    "summary": summary,
                    "url": url,
                    "id": url  # Use URL as unique ID for history
                })
    return items

def main():
    print("=== X Auto-Post Start ===")
    
    client = get_twitter_client()
    if not client:
        # Exit gracefully so we don't break the build if keys are missing
        print("Skipping X posting due to missing credentials.")
        return

    history = load_history()
    print(f"Loaded {len(history)} previously posted items.")
    
    # 1. Gather all news items from today's reports
    # Assuming reports are in reports/YYYY-MM-DD/*.md
    # Or just recursive search in reports/
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # We focus on the latest reports to avoid posting old stuff if the script runs locally
    # But strictly speaking, the history file prevents duplicates mostly.
    # Let's check all reports but only post if not in history.
    all_reports = glob.glob(os.path.join(REPORTS_DIR, "*", "*.md"))
    
    new_items_count = 0
    
    for report_path in all_reports:
        items = parse_report_file(report_path)
        
        for item in items:
            if item['id'] in history:
                continue
            
            print(f"New Item found: {item['tool']} - {item['summary'][:30]}...")
            
            # Construct Tweet
            # Max 280 chars. 
            # Format:
            # 📢 {Tool Name} Update!
            # {Summary}
            # {URL}
            # #AI #Tech
            
            tweet_text = f"📢 {item['tool']} Update!\n\n{item['summary']}\n\n{item['url']}\n#AI #{item['category'].replace(' ', '')}"
            
            # Truncate if too long (rough check, URL is 23 chars)
            if len(tweet_text) > 280:
                # Naive truncation
                excess = len(tweet_text) - 280
                item['summary'] = item['summary'][:-excess-5] + "..."
                tweet_text = f"📢 {item['tool']} Update!\n\n{item['summary']}\n\n{item['url']}\n#AI"

            try:
                # Dry run check could go here if implemented as an arg
                response = client.create_tweet(text=tweet_text)
                print(f"  -> Posted! Tweet ID: {response.data['id']}")
                
                history.append(item['id'])
                save_history(history) # Save immediately to avoid double post on crash
                new_items_count += 1
                
            except Exception as e:
                print(f"  -> Failed to post: {e}")
                
    if new_items_count == 0:
        print("No new items to post.")
    
    print("=== X Auto-Post Complete ===")

if __name__ == "__main__":
    main()
