import os
import re
import datetime
import glob
from collections import defaultdict

# Configuration
REPORTS_DIR = "reports"
DOCS_DIR = "docs"

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

        if "Updates not found" in body_text or "No significant news" in body_text or body_text.strip() == "":
            continue

        # Parse Date if available, else use file date
        date_match = re.search(r'(?:- )?\*\*Date\*\*:? (.*)', body_text)
        item_date = date_match.group(1).strip() if date_match else "Unknown Date"
        
        url_match = re.search(r'(?:- )?\*\*URL\*\*:? (.*)', body_text)
        summary_match = re.search(r'(?:- )?\*\*Summary\*\*:? (.*)', body_text)
        why_match = re.search(r'(?:- )?\*\*Why\*\*:? (.*)', body_text)
        
        url = url_match.group(1).strip() if url_match else "#"
        
        if summary_match:
            summary = summary_match.group(1).strip().replace("**", "")
        else:
            summary = body_text.replace("\n", "<br>")
            
        why = why_match.group(1).strip() if why_match else "Check details."

        items.append({
            "date": item_date,
            "category": category,
            "tool": tool_name,
            "summary": summary,
            "why": why,
            "url": url,
            "raw_text": body_text
        })
    return items

def generate_html_from_items(items, title):
    """Generates full HTML page from a list of news items."""
    content_html = ""
    
    # Sort items by Date (Newest first), then by Category
    # Assuming date format YYYY-MM-DD
    items.sort(key=lambda x: x['date'], reverse=True)
    
    current_date = None
    
    for item in items:
        # Date Header Grouping
        if item['date'] != current_date:
            current_date = item['date']
            content_html += f'<h2 class="category-title" style="margin-top:40px;">{current_date}</h2>'

        card = f"""
        <div class="news-card">
            <div class="news-header">
                <div class="tool-name">{item['tool']} <span style="font-size:0.8em; font-weight:400; color:#aaa; margin-left:10px;">({item['category']})</span></div>
            </div>
            <div class="news-content">
                <p><strong>{item['summary']}</strong></p>
                <p style="margin-top: 10px; font-size: 0.9em; color: #aaa;"><i class="fas fa-info-circle"></i> {item['why']}</p>
            </div>
            <div class="news-footer">
                <a href="{item['url']}" target="_blank" class="source-link">View Post</a>
            </div>
        </div>
        """
        content_html += card
        
    if not content_html:
        content_html = "<div class='no-news'>No news found for this period.</div>"
        
    return HTML_HEADER.format(page_title=title) + content_html + HTML_FOOTER

def build():
    print("Starting build process...")
    
    # Grid search all reports
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
    
    index_html = generate_html_from_items(latest_items, "Latest News (3 Days)")
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
    
    for month, items in sorted(months.items(), reverse=True):
        filename = f"archive_{month}.html"
        month_html = generate_html_from_items(items, f"Archive: {month}")
        with open(os.path.join(DOCS_DIR, filename), 'w', encoding='utf-8') as f:
            f.write(month_html)
        print(f"Generated {filename}")
        
        archive_links_html += f"<li style='margin:10px 0;'><a href='{filename}' style='color:white; font-size:1.2em;'>{month} ({len(items)} items)</a></li>"

    archive_links_html += "</ul>"
    
    # 3. Generate Archives Index
    archives_page = HTML_HEADER.format(page_title="Archives") + archive_links_html + HTML_FOOTER
    with open(os.path.join(DOCS_DIR, "archives.html"), 'w', encoding='utf-8') as f:
        f.write(archives_page)
    print("Generated archives.html")

if __name__ == "__main__":
    build()
