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

import google.generativeai as genai

def select_top_news_with_gemini(all_items):
    """Uses Gemini 3 Flash to curate the top 10 most important news."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ No GEMINI_API_KEY found. Falling back to simple selection.")
        return all_items[:10]

    print(f"🧠 Asking Gemini 3 Flash to curate {len(all_items)} items...")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    # User requested specific model: Gemini 3 Flash Preview
    # Note: If this specific model ID is not yet active in region, standard flash might be used.
    # We will try the user's requested ID, fallback to 'gemini-2.0-flash-exp' if 3 is not out 
    # (But based on search, 3 is available).
    model_name = 'gemini-3-flash-preview' 
    
    try:
        model = genai.GenerativeModel(model_name)
        
        # Prepare content for AI
        news_text = "\n\n".join(all_items)
        
        prompt = (
            "Role: 敏腕ビジネス誌編集長 (Target: 日本の40代ビジネスパーソン・一般層)\n"
            "Task: 以下のAIニュースリストから、「今の時代を生きる大人にとって、本当に知っておくべきトップ10」を厳選してください。\n\n"
            "【選定基準 - Selection Criteria】\n"
            "1. **社会的インパクト**: 仕事のやり方、生活、社会のルールを変えるようなニュースを最優先（例: ChatGPTの新機能、Googleの革命的発表）。\n"
            "2. **実用性**: 「明日から自分の仕事や生活に使えるか？」を重視。マニアックな開発者向けツール（APIの微細な変更、ライブラリ更新など）は思い切って除外してください。\n"
            "3. **トレンド**: 「今、世の中で何が起きているか」を把握できる大きな動き。\n\n"
            "【執筆スタイル - Tone & Style】\n"
            "・40代の知的な大人に向けた、落ち着いたプロフェッショナルな日本語。\n"
            "・専門用語は噛み砕き、「なぜそれが凄いのか」「どう役に立つのか」という**意味（Implication）**を解説してください。\n\n"
            "【出力フォーマット】\n"
            "必ず以下の形式でトップ10を出力してください。\n\n"
            "1. **キャッチーな見出し** (ツール名)\n"
            "   概要: [何が起きたのか、簡潔に]\n"
            "   💡 視点: [なぜこれが重要なのか？ビジネスや生活への影響は？]\n"
            "\n"
            "(以下、10位まで続ける)\n\n"
            "News List:\n"
            f"{news_text[:35000]}" # Increased limit slightly for context
        )
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            print("✅ Gemini curation successful!")
            return [response.text.strip()] # Return as a single pre-formatted string block
            
    except Exception as e:
        print(f"❌ Gemini Curation Failed: {e}")
        return all_items[:10] # Fallback

    return all_items[:10]

def main():
    # TIMEZONE FIX: GitHub Actions runs in UTC. Force JST (UTC+9)
    JST = datetime.timezone(datetime.timedelta(hours=9))
    now_jst = datetime.datetime.now(JST)
    
    print(f"Current JST Time: {now_jst.strftime('%H:%M')}")
    
    # Only run at 7:00 AM 
    if now_jst.hour != 7:
        print("🕒 Not 7:00 AM JST. Skipping LINE post.")
        return

    print("=== LINE Auto-Post Start ===")
    
    items, date_str = get_latest_report_items()
    
    if not items:
        print("No news items found for today.")
        return

    # AI Curation Step
    # If using AI, we get a single string block. If fallback, we get list.
    curated_content = select_top_news_with_gemini(items)
    
    # Construct Message
    msg = f"📅 {date_str} AI News Digest (AI Selected)\n\n"
    
    if isinstance(curated_content, list) and len(curated_content) == 1 and "\n" in curated_content[0]:
        # It's the AI text block
        msg += curated_content[0]
    else:
        # Fallback list
        msg += "\n\n".join(curated_content)
    
    # Footer
    msg += f"\n\n🔗 Full Report:\n{SITE_URL}"
    
    print("Generated Message:")
    print(msg)
    
    send_line_message(msg)
    print("=== LINE Auto-Post Complete ===")

if __name__ == "__main__":
    main()
