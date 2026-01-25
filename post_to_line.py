import os
import glob
import datetime
import re
from dotenv import load_dotenv
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApi,
    PushMessageRequest,
    BroadcastRequest,
    TextMessage,
)

# Load environment variables
load_dotenv()

# Configuration
REPORTS_DIR = "reports"
SITE_URL = "https://tadahikof.github.io/AI_TOOL_NEWS/"  # Adjust to your actual Pages URL

def get_latest_report_items():
    """Finds today's report and extracts news items."""
    # TIMEZONE FIX: GitHub Actions runs in UTC. Force JST (UTC+9)
    JST = datetime.timezone(datetime.timedelta(hours=9))
    today_str = datetime.datetime.now(JST).strftime("%Y-%m-%d")
    
    # Also check yesterday just in case of boundary issues, but prioritize today
    target_dirs = [today_str]
    
    all_items = []
    
    today_folder = os.path.join(REPORTS_DIR, today_str)
    
    # User Request: RSS General News ONLY (No Tool Updates)
    # Collected at 7:00 AM, covering previous 24h.
    # We only look at 'general_news' subfolder in today's report dir.
    
    target_path = os.path.join(today_folder, "general_news", "*.md")
    files = glob.glob(target_path)
    
    all_items = []
    for fpath in files:
        items = parse_report_file(fpath)
        all_items.extend(items)
    
    return all_items, today_str

def parse_report_file(filepath):
    """Parses a markdown report to extract news items (Same logic as post_to_x)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by tool sections (## ToolName)
    sections = re.split(r'^## ', content, flags=re.MULTILINE)[1:]
    
    items = []
    for section in sections:
        lines = section.strip().split('\n')
        tool_name = lines[0].strip()
        body_text = "\n".join(lines[1:]).strip()

        if "Updates not found" in body_text or "No significant news" in body_text or not body_text:
            continue
        
        summary_match = re.search(r'(?:- )?\*\*Summary\*\*:? (.*)', body_text)
        url_match = re.search(r'(?:- )?\*\*URL\*\*:? (.*)', body_text)
        
        if summary_match:
            summary = summary_match.group(1).strip().replace("**", "")
            items.append(f"🔹 {tool_name}\n{summary[:50]}...") # Truncate for LINE readability
            
    return items

def send_line_message(message_text):
    """Sends a push message to LINE."""
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    
    if not token or not user_id:
        print("Skipping LINE post: Missing credentials.")
        return

    configuration = Configuration(access_token=token)
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            
            # BROADCAST MODE (Send to ALL followers)
            # Was: PushMessageRequest(to=user_id, ...)
            broadcast_request = BroadcastRequest(
                messages=[TextMessage(text=message_text)]
            )
            line_bot_api.broadcast(broadcast_request)
            print("Successfully sent LINE BROADCAST message.")
    except Exception as e:
        print(f"Failed to send LINE message: {e}")

def main():
    # TIMEZONE FIX: GitHub Actions runs in UTC. Force JST (UTC+9)
    JST = datetime.timezone(datetime.timedelta(hours=9))
    now_jst = datetime.datetime.now(JST)
    
    print(f"Current JST Time: {now_jst.strftime('%H:%M')}")
    
    # Only run at 7:00 AM (allow minute variance 00-59 if cron is delayed, but usually runs on hour)
    # Since cron is '0 * * * *', it runs at :00.
    if now_jst.hour != 7:
        print("🕒 Not 7:00 AM JST. Skipping LINE post.")
        # Optional: Allow override via argument for testing?
        # For now, strictly exit.
        return

    print("=== LINE Auto-Post Start ===")
    
    items, date_str = get_latest_report_items()
    
    if not items:
        print("No news items found for today.")
        return

    # Construct the message
    # Header
    msg = f"📅 {date_str} AI News Digest\n\n"
    
    # Body (Top 10 items to avoid limit)
    msg += "\n\n".join(items[:10])
    
    if len(items) > 10:
        msg += f"\n\n...and {len(items)-10} more."
    
    # Footer
    msg += f"\n\n🔗 Full Report:\n{SITE_URL}"
    
    print("Generated Message:")
    print(msg)
    
    send_line_message(msg)
    print("=== LINE Auto-Post Complete ===")

if __name__ == "__main__":
    main()
