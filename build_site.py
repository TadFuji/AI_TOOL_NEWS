import os
import re
import datetime
import glob
import json
from collections import defaultdict
from dateutil import parser

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# Embedded HTML Template (Simple & Clean)
HTML_HEADER = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI TOOL NEWS</title>
    <link rel="stylesheet" href="styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>

    <div class="container">
        <header>
            <h1>AI TOOL NEWS</h1>
            <div class="date-badge"><i class="far fa-calendar-alt"></i> {page_title}</div>
            <nav style="margin-top: 15px;">
                <a href="index.html" style="color:white; margin-right:15px; text-decoration:none;">Latest</a>
                <a href="archives.html" style="color:white; text-decoration:none;">Archives</a>
            </nav>
        </header>

        <div class="news-feed">
"""

HTML_FOOTER = """
        </div>

        <footer style="text-align: center; margin-top: 60px; color: #888; font-size: 0.8rem;">
            <p>Powered by Grok-4 & Antigravity Operations</p>
        </footer>
    </div>
</body>
</html>
"""

def parse_report_file(filepath):
    """Parses a markdown report and returns a list of news items (dicts)."""
    items = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract Category
    cat_match = re.search(r'# (.*?) - Daily Report', content)
    category = cat_match.group(1) if cat_match else "Uncategorized"

    sections = re.split(r'^## ', content, flags=re.MULTILINE)[1:]
    
    for section in sections:
        lines = section.strip().split('\n')
        tool_name = lines[0].strip()
        body_text = "\n".join(lines[1:]).strip()

        # Check for empty report immediately
        if "No recent posts" in body_text or "Updates not found" in body_text or body_text.strip() == "":
            continue

        # Split by "- Post:" to support multiple posts per tool
        # Adding a lookahead or just splitting and filtering empty chunks
        # The markdown format usually is "- Post: ... \n - Time: ... "
        # We start by splitting by correct marker.
        # Note: The first post might start immediately or after some newlines.
        
        # Normalize body text (ensure it starts with - Post if it's there)
        # But sometimes it might just be text.
        
        # Strategy: Find all occurrences of "- Post:" and their indices
        # If no "- Post:" found, treat whole body as one item (legacy)
        
        post_blocks = []
        if "- Post:" in body_text:
            # Split by - Post:, but keep the delimiter or prepend it back
            # re.split with capturing group creates chunks: [pre, - Post:, content, - Post:, content...]
            # Simpler: raw string split
            raw_chunks = body_text.split("- Post:")
            
            # First chunk is usually empty or headers, unless file doesn't start with - Post:
            # If body_text starts with "- Post:", raw_chunks[0] is empty.
            
            for chunk in raw_chunks:
                if not chunk.strip(): continue
                # We stripped "- Post:", so add it back to make regex work or adjust regex
                post_blocks.append(chunk.strip())
        else:
            post_blocks = [body_text]

        for block in post_blocks:
            # If we split by "- Post:", the block content starts immediately with the post text content (or "Summary")
            # The regex needs to handle "Summary" starting logically at start of string
            
            # Parse Date
            # Support multiple formats: "**Date**: ...", "Time: ...", "- Time: ..."
            date_match = re.search(r'(?:- )?(?:\*\*Date\*\*|Time):? (.*)', block)
            item_date_raw = date_match.group(1).strip() if date_match else "Unknown Date"
            
            # Skip if unknown date and it looks empty (double check)
            if item_date_raw == "Unknown Date" and len(block) < 20: 
                continue

            # Parse URL
            url_match = re.search(r'(?:- )?(?:\*\*URL\*\*|URL):? (.*)', block)
            url = url_match.group(1).strip() if url_match else "#"
            
            # Parse Summary/Post Text
            # It's everything before Time/URL usually.
            # Regex: Start of block until Time or URL
            # Or just take the lines valid.
            
            # If we split by "- Post:", block is just the content.
            # But we need to exclude metadata lines (Time:, URL:) from summary
            
            summary_lines = []
            for line in block.split('\n'):
                if re.match(r'(?:- )?(?:\*\*Date\*\*|Time):', line): continue
                if re.match(r'(?:- )?(?:\*\*URL\*\*|URL):', line): continue
                if re.match(r'(?:- )?(?:\*\*Summary\*\*|Post):', line): continue # In case it was left over
                summary_lines.append(line)
            
            summary = "\n".join(summary_lines).strip()
            # Clean up ** wrappers if present from old parsing
            summary = summary.replace("**Post**", "").strip()
            if summary.startswith(":"): summary = summary[1:].strip()
            
            summary = summary.replace("\n", "<br>")

            why = "Check details." # Default why

            # Date Processing
            display_date = item_date_raw
            sort_date = item_date_raw
            item_date = "Unknown Date"

            try:
                clean_date = re.sub(r'\(?(GMT|UTC)\)?', '', item_date_raw).strip()
                dt = parser.parse(clean_date)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                jst = datetime.timezone(datetime.timedelta(hours=9))
                dt_jst = dt.astimezone(jst)
                
                display_date = dt_jst.strftime("%Y年%m月%d日 %H時%M分")
                sort_date = dt_jst.strftime("%Y-%m-%d %H:%M")
                item_date = dt_jst.strftime("%Y-%m-%d")
            except:
                 # Fallback regex
                 match = re.search(r'(\d{4}-\d{2}-\d{2})', item_date_raw)
                 if match:
                     item_date = match.group(1)
                 elif item_date_raw != "Unknown Date" and len(item_date_raw) >= 10:
                     item_date = item_date_raw[:10]
            
            items.append({
                "date": item_date,
                "sort_date": sort_date,
                "display_date": display_date,
                "category": category,
                "tool": tool_name,
                "summary": summary,
                "why": why,
                "url": url,
                "raw_text": block
            })

    return items

def load_targets():
    """Laws targets.json to map tool names to twitter handles."""
    targets_path = os.path.join(BASE_DIR, "targets.json")
    tool_map = {}
    try:
        with open(targets_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Flatten the list structure
            for category in data:
                for tool in category.get('tools', []):
                    tool_map[tool['name']] = tool
        return tool_map
    except Exception as e:
        print(f"Warning: Could not load targets.json: {e}")
        return {}

def generate_html_from_items(items, title, tool_map):
    """Generates full HTML page from a list of news items."""
    content_html = ""
    
    # Sort items by Date (Newest first), then by Category
    # Use sort_date for full precision
    items.sort(key=lambda x: x.get('sort_date', x['date']), reverse=True)
    
    current_date = None
    
    # Regex for valid tweet URL (simple validation)
    tweet_pattern = re.compile(r'https?://(www\.)?(twitter|x)\.com/[a-zA-Z0-9_]+/status/\d+')

    # Deduplication Logic
    seen = set()
    unique_items = []
    for item in items:
        # Create a unique signature for the news item
        # URL is the most reliable unique identifier for a social media post
        key = item['url'].strip()
        
        # Fallback for manual/weird entries without URL (rare)
        if not key or key == "#":
            summary_key = re.sub(r'\s+', '', item['summary'])[:30].lower()
            key = f"{item['tool']}_{item['date']}_{summary_key}"
        
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(item)
    
    # Use unique_items for generation
    for item in unique_items:
        # Date Header Grouping
        if item['date'] != current_date:
            current_date = item['date']
            content_html += f'<h2 class="category-title" style="margin-top:40px;">{current_date}</h2>'

        # Resolve accounts for search fallback
        # item['tool'] is the key in targets.json
        accounts = tool_map.get(item['tool'], {}).get('accounts', [])
        # Default to tool name if no account found (fallback)
        primary_account = accounts[0] if accounts else item['tool'].replace(" ", "")
        
        search_query = f"from:{primary_account}"
        search_url = f"https://x.com/search?q={search_query}&src=typed_query&f=live"

        # Static Validation of Primary URL
        valid_url = item['url']
        is_suspicious = False
        
        if not tweet_pattern.match(valid_url):
            is_suspicious = True
            # If invalid/suspicious, we can strictly replace it OR just rely on the user.
            # Decision: Keep the link but style it differently or just rely on fallback?
            # User request: "Rewrite valid URL... if suspicious... to search result page"
            # Let's replace it to be safe.
            valid_url = search_url
            
        card_buttons = f"""
            <div class="news-footer" style="display: flex; gap: 10px;">
                <a href="{valid_url}" target="_blank" class="source-link">
                    { '投稿を見る' if not is_suspicious else '⚠️ 検索結果 (自動修正)' }
                </a>
                <a href="{search_url}" target="_blank" class="source-link" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2);">
                    🔍 検証する
                </a>
            </div>
        """

        card = f"""
        <div class="news-card">
            <div class="news-header">
                <div class="tool-name">
                    {item['tool']} 
                    <span style="font-size:0.8em; font-weight:400; color:#aaa; margin-left:10px;">({item['category']})</span>
                </div>
                <div class="post-date" style="font-size:0.75em; color:#888; margin-top:2px;">
                    <i class="far fa-clock"></i> {item['display_date']}
                </div>
            </div>
            <div class="news-content">
                <p><strong>{item['summary']}</strong></p>
                <p style="margin-top: 10px; font-size: 0.9em; color: #aaa;"><i class="fas fa-info-circle"></i> {item['why']}</p>
            </div>
            {card_buttons}
        </div>
        """
        content_html += card
        
    if not content_html:
        content_html = "<div class='no-news'>期間内のニュースは見つかりませんでした。</div>"
        
    return HTML_HEADER.format(page_title=title) + content_html + HTML_FOOTER

def build():
    print("Starting build process...")
    
    # Load targets for account mapping
    tool_map = load_targets()

    # Grid search all reports
    # Tool Reports (Root of day folder)
    all_reports = glob.glob(os.path.join(REPORTS_DIR, "*", "*.md"))
    
    all_items = []
    for report_path in all_reports:
        # We can extract the file date from the parent folder name if needed
        # But for now we parse the file content
        items = parse_report_file(report_path)
        all_items.extend(items)
        
    print(f"Total News Items Found: {len(all_items)}")

    # 1. Generate Index (Latest 3 Days)
    # Get unique dates present in items
    unique_dates = sorted(list(set(i['date'] for i in all_items if i['date'] != 'Unknown Date')), reverse=True)
    latest_3_dates = unique_dates[:3]
    
    latest_items = [i for i in all_items if i['date'] in latest_3_dates]
    
    index_html = generate_html_from_items(latest_items, "Latest News (3 Days)", tool_map)
    with open(os.path.join(DOCS_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html)
    print("Generated index.html")

    # 2. Generate Monthly Archives
    # Group by YYYY-MM
    months = defaultdict(list)
    for item in all_items:
        if item['date'] == 'Unknown Date': continue
        month_key = item['date'][:7] # YYYY-MM
        months[month_key].append(item)
        
    archive_links_html = "<h2>Monthly Archives</h2><ul style='list-style:none; padding:0;'>"
    
    # Optimization: Only rebuild recent months
    JST = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(JST)
    current_month = now.strftime("%Y-%m")
    # Simple logic for prev month (handle year rollover loosely or just use library)
    # Actually, easiest is just to parse year/month
    # Let's just update "This Month" and "Last Month" (calculated robustly)
    
    # Calculate Previous Month string
    first_day = now.replace(day=1)
    prev_month_date = first_day - datetime.timedelta(days=1)
    prev_month = prev_month_date.strftime("%Y-%m")
    
    targets_to_build = {current_month, prev_month}
    
    print(f"⚡ Incremental Build Active. Targets: {targets_to_build}")
    
    for month, items in sorted(months.items(), reverse=True):
        filename = f"archive_{month}.html"
        filepath = os.path.join(DOCS_DIR, filename)
        
        # Build if:
        # 1. It is a target month (Current/Prev)
        # 2. File doesn't exist yet (New historical import?)
        # 3. Always force build if user manually flushes (not implemented, but safe default)
        
        if month in targets_to_build or not os.path.exists(filepath):
            month_html = generate_html_from_items(items, f"Archive: {month}", tool_map)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(month_html)
            print(f"  -> Rebuilt: {filename}")
        else:
            print(f"  -> Skipped (Cached): {filename}")
        
        # Add to Index Link (Always needed)
        archive_links_html += f"<li style='margin:10px 0;'><a href='{filename}' style='color:white; font-size:1.2em;'>{month} ({len(items)} items)</a></li>"

    archive_links_html += "</ul>"
    
    # 3. Generate Archives Index
    archives_page = HTML_HEADER.format(page_title="Archives") + archive_links_html + HTML_FOOTER
    with open(os.path.join(DOCS_DIR, "archives.html"), 'w', encoding='utf-8') as f:
        f.write(archives_page)
    print("Generated archives.html")

if __name__ == "__main__":
    build()
