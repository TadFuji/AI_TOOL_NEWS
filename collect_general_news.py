import os
import json
import feedparser
import datetime
from dateutil import parser as date_parser
from datetime import timezone

# --- CONFIGURATION (Ported from legacy bot) ---
RSS_FEEDS = [
    # --- US Major Media ---
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "region": "US"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "region": "US"},
    {"name": "Wired AI", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "region": "US"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "region": "US"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "region": "US"},
    {"name": "Ars Technica AI", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "region": "US"},
    {"name": "ZDNet AI", "url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml", "region": "US"},
    {"name": "The Information", "url": "https://www.theinformation.com/feed", "region": "US"},
    # --- Official Blogs ---
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "region": "US"},
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss.xml", "region": "US"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "region": "US"},
    {"name": "DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml", "region": "UK"},
    {"name": "Microsoft AI Blog", "url": "https://blogs.microsoft.com/ai/feed/", "region": "US"},
    # --- Japan ---
    {"name": "NHK Science", "url": "https://www.nhk.or.jp/rss/news/cat6.xml", "region": "JP"},
    {"name": "ITmedia AI+", "url": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml", "region": "JP"},
    # --- Europe/Global ---
    {"name": "BBC Technology", "url": "https://feeds.bbci.co.uk/news/technology/rss.xml", "region": "UK"},
    {"name": "Reuters Technology", "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best&best-topics=tech", "region": "UK"},
]

AI_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "deep learning", "neural network",
    "transformer", "generative AI", "LLM", "GPT", "Gemini", "Claude", "Copilot",
    "Midjourney", "Stable Diffusion", "OpenAI", "Anthropic", "DeepMind", "xAI",
    "NVIDIA", "Hugging Face", "GPU", "robotics", "autonomous", "agent",
    "生成AI", "人工知能", "機械学習", "大規模言語モデル",
]

BASE_REPORT_DIR = "reports"

def setup_report_dir():
    """Creates a directory for today's reports."""
    JST = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(JST).strftime("%Y-%m-%d")
    path = os.path.join(BASE_REPORT_DIR, today, "general_news") # Subfolder for general news
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def is_ai_news(title, summary):
    """Simple keyword filtering to ensure relevance."""
    content = (title + " " + summary).lower()
    return any(k.lower() in content for k in AI_KEYWORDS)

def collect_from_rss():
    # TIMEZONE FIX: GitHub Actions runs in UTC. Force JST (UTC+9)
    JST = datetime.timezone(datetime.timedelta(hours=9))
    now_jst = datetime.datetime.now(JST)
    
    # User Request: General News is collected ONCE per day at 7:00 AM
    if now_jst.hour != 7:
        print("🕒 Not 7:00 AM JST. Skipping General News (RSS) collection.")
        return

    print("=== General AI News Collection (RSS) Start ===")
    
    report_dir = setup_report_dir()
    JST = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(JST)
    cutoff = now - datetime.timedelta(hours=24) # Collect within last 24 hours
    
    count = 0
    
    for feed_info in RSS_FEEDS:
        print(f"📡 Checking {feed_info['name']}...")
        try:
            feed = feedparser.parse(feed_info["url"])
            
            for entry in feed.entries:
                # 1. Date Check
                pub_date = None
                if hasattr(entry, "published"):
                    pub_date = entry.published
                elif hasattr(entry, "updated"):
                    pub_date = entry.updated
                
                parsed_date = None
                if pub_date:
                    try:
                        parsed_date = date_parser.parse(pub_date)
                        if parsed_date.tzinfo is None:
                            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    except:
                        pass
                
                # Check if new enough (within 24h)
                # Note: Rough comparison as timezone handling in RSS varies
                if not parsed_date:
                    continue # Skip undated
                
                # Normalize to UTC for comparison if needed, or just lazy check
                # Simple Logic: If parsed_date > cutoff
                # (Handling TZ awareness issue requires care)
                try:
                    if parsed_date < cutoff:
                        continue 
                except:
                    # If comparison fails due to TZ offset mismatch, blindly accept recent items 
                    # from known feeds usually works, but safe to skip to avoid noise.
                    pass

                # 2. Keyword Check
                title = entry.title if hasattr(entry, "title") else ""
                summary = entry.summary if hasattr(entry, "summary") else ""
                link = entry.link if hasattr(entry, "link") else ""
                
                if not is_ai_news(title, summary):
                    continue

                # 3. Save Report
                count += 1
                safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
                filename = f"GEN_{count}_{safe_title}.md"
                filepath = os.path.join(report_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"- **Source**: {feed_info['name']}\n")
                    f.write(f"- **Date**: {parsed_date}\n")
                    f.write(f"- **URL**: {link}\n\n")
                    f.write(f"## Summary\n{summary}\n")
                
                print(f"  -> Found: {title[:40]}...")

        except Exception as e:
            print(f"  -> Error parsing {feed_info['url']}: {e}")
            
    print(f"=== Collection Complete. Found {count} items. ===")

if __name__ == "__main__":
    collect_from_rss()
