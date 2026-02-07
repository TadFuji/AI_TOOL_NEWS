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
            <nav>
                <a href="index.html" class="nav-link {active_latest}">Latest</a>
                <a href="archives.html" class="nav-link {active_archives}">Archives</a>
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

def clean_summary_text(text, url=None, date=None):
    """Clean up markdown markers, redundant info, dates, and URLs from summary text."""
    # 1. Extract embedded URLs from the text before cleaning
    embedded_urls = re.findall(r'https?://\S+', text)
    
    summary_lines = []
    for line in text.split('\n'):
        # Strip out the markers
        clean_line = line.strip()
        clean_line = re.sub(r'^(?:- )?(?:Post|Time|URL|\*\*Date\*\*|\*\*Summary\*\*|\*\*URL\*\*):', '', clean_line, flags=re.IGNORECASE).strip()
        
        if clean_line:
            # Skip if line is JUST a date or JUST a URL
            if (url and clean_line == url) or (date and clean_line == date):
                continue
            
            # Remove date patterns like YYYY-MM-DD HH:MM
            clean_line = re.sub(r'\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?', '', clean_line).strip()
            
            # Remove URLs from the text line
            clean_line = re.sub(r'https?://\S+', '', clean_line).strip()
            
            if clean_line:
                summary_lines.append(clean_line)
    
    summary = " ".join(summary_lines).strip()
    # Clean up ** wrappers
    summary = summary.replace("**", "").strip()
    summary = summary.replace("\n", " ").replace("  ", " ")
    
    return summary, embedded_urls



def load_targets():
    """Loads targets.json to map tool names to twitter handles."""
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
    
    # Determine active tab classes
    active_latest = "active-latest" if "Latest" in title else ""
    active_archives = "active-archives" if "Archive" in title else ""
    
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
        
        # Skip items with "No significant news found" in summary
        if "No significant news found" in item['summary'] or "no significant news found" in item['summary'].lower():
            continue
            
        unique_items.append(item)
    
    # Use unique_items for generation
    for item in unique_items:
        # Date Header Grouping
        if item['date'] != current_date:
            current_date = item['date']
            content_html += f'<h2 class="category-title">{current_date}</h2>'

        # Resolve accounts for search fallback
        accounts = tool_map.get(item['tool'], {}).get('accounts', [])
        primary_account = accounts[0] if accounts else item['tool'].replace(" ", "")
        
        search_query = f"from:{primary_account}"
        search_url = f"https://x.com/search?q={search_query}&src=typed_query&f=live"

        # Primary URL from X
        valid_url = item['url']
        is_suspicious = False
        
        if not tweet_pattern.match(valid_url):
            is_suspicious = True
            valid_url = search_url
            
        # Optional Reference URL
        ref_btn = ""
        if item.get('ref_url'):
            ref_btn = f"""
                <a href="{item['ref_url']}" target="_blank" class="source-link">
                    <i class="fas fa-external-link-alt"></i> 参照資料
                </a>
            """

        card_buttons = f"""
            <div class="news-footer">
                <a href="{valid_url}" target="_blank" class="source-link">
                    <i class="fab fa-x-twitter"></i> { '投稿を見る' if not is_suspicious else '⚠️ 検索結果' }
                </a>
                {ref_btn}
            </div>
        """

        # Define score
        score = int(item.get('score', 3))

        # Build importance tags
        impact_class = ""
        stars = ""
        if score >= 5:
            impact_class = "groundbreaking"
            stars = f'<span class="importance-badge score-5-tag"><i class="fas fa-bolt"></i> MAJOR</span>'
        elif score >= 4:
            impact_class = "high-impact"
            stars = f'<span class="importance-badge score-4-tag"><i class="fas fa-fire"></i> PICK UP</span>'

        card = f"""
        <div class="news-card {impact_class}">
            <div class="news-header">
                <div class="tool-name">
                    <span class="name">{item['tool']}</span>
                    {stars}
                </div>
                <div class="post-date">
                    <i class="far fa-clock"></i> {item['display_date']}
                </div>
            </div>
            <div class="news-content">
                <p><strong>{item['summary']}</strong></p>
                <div class="why-section">
                    <i class="fas fa-info-circle"></i> {item['why']}
                </div>
            </div>
            {card_buttons}
        </div>
        """
        content_html += card
        
    if not content_html:
        content_html = "<div class='no-news'>期間内のニュースは見つかりませんでした。</div>"
        
    # If it's the latest page, the navigation link already shows the status clearly.
    # Hide the redundant title for the index page.
    header_html = ""
    if "Latest" not in title:
        header_html = f'<div style="text-align:center; margin-bottom:40px;"><h2 class="category-title">{title}</h2></div>'

    return HTML_HEADER.format(active_latest=active_latest, active_archives=active_archives) + header_html + content_html + HTML_FOOTER

def load_all_reports():
    """Scans JSON reports and parses them into news items."""
    all_items = []
    
    # Grid search all JSON reports (New Standard)
    json_reports = glob.glob(os.path.join(REPORTS_DIR, "*", "*.json"))
    print(f"  Scanning {len(json_reports)} JSON reports...")
    for path in json_reports:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Normalize JSON data to the item format
                # Note: We still use the date processing logic inside our build
                item_date_raw = data.get('post_date', 'Unknown Date')
                summary_raw = data.get('summary', '')
                url_main = data.get('url', '#')
                
                # Use helper for consistency
                clean_text, ext_urls = clean_summary_text(summary_raw, url=url_main, date=item_date_raw)
                ref_url = ext_urls[0] if ext_urls and ext_urls[0] != url_main else None

                item = {
                    "raw_date": item_date_raw,
                    "category": data.get('category', 'Uncategorized'),
                    "tool": data.get('tool', 'Unknown'),
                    "summary": clean_text,
                    "why": data.get('why', '詳細をご確認ください。'),
                    "score": data.get('score', 3),
                    "ref_url": ref_url,
                    "url": url_main,
                }
                
                # Apply date logic
                item.update(process_item_date(item_date_raw))
                
                if "No significant news found" not in item['summary']:
                    all_items.append(item)
        except Exception as e:
            print(f"    ⚠️ Error parsing JSON {path}: {e}")

    return all_items

def process_item_date(date_raw):
    """Helper to unify date processing."""
    display_date = date_raw
    sort_date = date_raw
    item_date = "Unknown Date"

    try:
        clean_date = re.sub(r'\(?(GMT|UTC|JST)\)?', '', date_raw).strip()
        dt = parser.parse(clean_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        jst = datetime.timezone(datetime.timedelta(hours=9))
        dt_jst = dt.astimezone(jst)
        
        display_date = dt_jst.strftime("%Y年%m月%d日 %H時%M分")
        sort_date = dt_jst.strftime("%Y-%m-%d %H:%M")
        item_date = dt_jst.strftime("%Y-%m-%d")
    except:
         match = re.search(r'(\d{4}-\d{2}-\d{2})', date_raw)
         if match:
             item_date = match.group(1)
         elif date_raw != "Unknown Date" and len(date_raw) >= 10:
             item_date = date_raw[:10]
    
    return {
        "date": item_date,
        "sort_date": sort_date,
        "display_date": display_date
    }

def build():
    print("Starting build process...")
    
    # Load targets for account mapping
    tool_map = load_targets()

    # Load all items from both formats
    all_items = load_all_reports()
    
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
        
    archive_links_html = '<div class="archive-grid">'
    
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
        # 3. Forced re-build (Environment variable or flag)
        
        force_rebuild = os.environ.get("FORCE_REBUILD") == "true"
        
        if month in targets_to_build or not os.path.exists(filepath) or force_rebuild:
            month_items = sorted(items, key=lambda x: x.get('sort_date', x['date']), reverse=True)
            month_html = generate_html_from_items(month_items, f"Archive: {month}", tool_map)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(month_html)
            print(f"  -> Rebuilt: {filename}")
        else:
            print(f"  -> Skipped (Cached): {filename}")
        
        # Add to Index Link (Always needed)
        archive_links_html += f"""
            <a href='{filename}' class='archive-item-link'>
                <div class='archive-card'>
                    <div class='archive-card-content'>
                        <i class='far fa-calendar-alt archive-icon'></i>
                        <span class='archive-month-text'>{month}</span>
                    </div>
                    <div class='archive-badge'>{len(items)} items</div>
                </div>
            </a>
        """

    archive_links_html += "</div>"
    
    # 3. Generate Archives Index
    # Use active_archives class
    header_html = '<div style="text-align:center; margin-bottom:60px;"><h2 class="category-title">Select Month</h2></div>'
    archives_page = HTML_HEADER.format(active_latest="", active_archives="active-archives") + header_html + archive_links_html + HTML_FOOTER
    with open(os.path.join(DOCS_DIR, "archives.html"), 'w', encoding='utf-8') as f:
        f.write(archives_page)
    print("Generated archives.html")

if __name__ == "__main__":
    build()
