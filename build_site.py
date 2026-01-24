import os
import re
import datetime
import glob

# Configuration
REPORTS_DIR = "reports"
DOCS_DIR = "docs"
TEMPLATE_FILE = "template.html" # We will embed this or read it

# Embedded HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI TOOL NEWS | Daily Update</title>
    <link rel="stylesheet" href="styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>

    <div class="container">
        <header>
            <h1>AI TOOL NEWS</h1>
            <div class="date-badge"><i class="far fa-calendar-alt"></i> {date_str}</div>
        </header>

        <div class="news-feed">
            {content_html}
        </div>

        <footer style="text-align: center; margin-top: 60px; color: #888; font-size: 0.8rem;">
            <p>Powered by Grok-4 & Antigravity Operations</p>
        </footer>
    </div>
</body>
</html>
"""

def get_latest_report_date():
    """Finds the most recent date folder in reports."""
    dates = [d for d in os.listdir(REPORTS_DIR) if os.path.isdir(os.path.join(REPORTS_DIR, d))]
    if not dates:
        return None
    dates.sort(reverse=True)
    return dates[0]

def parse_markdown_file(filepath):
    """Parses a category markdown file and returns HTML for cards."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract Category Title
    category_match = re.search(r'# (.*?) - Daily Report', content)
    category_title = category_match.group(1) if category_match else "Uncategorized"

    # Split by Tool Sections (## Tool Name)
    sections = re.split(r'^## ', content, flags=re.MULTILINE)[1:] # Skip preamble
    
    cards_html = ""
    
    for section in sections:
        lines = section.strip().split('\n')
        tool_name = lines[0].strip()
        body_text = "\n".join(lines[1:]).strip()

        # Check if "Updates not found" or "No significant news"
        if "Updates not found" in body_text or "No significant news" in body_text or body_text.strip() == "":
            continue # Skip empty cards

        # Parse Fields (Date, URL, Importance, Summary, Why)
        url_match = re.search(r'(?:- )?\*\*URL\*\*:? (.*)', body_text)
        summary_match = re.search(r'(?:- )?\*\*Summary\*\*:? (.*)', body_text)
        why_match = re.search(r'(?:- )?\*\*Why\*\*:? (.*)', body_text)
        
        url = url_match.group(1).strip() if url_match else "#"
        
        # IMPROVED FALLBACK: If summary regex fails, use the whole body text (truncated)
        if summary_match:
            summary = summary_match.group(1).strip().replace("**", "")
        else:
            # Clean up the body text for display
            summary = body_text.replace("\n", "<br>")
        
        why = why_match.group(1).strip() if why_match else "Check details in post."

        # Generate Card HTML
        card = f"""
        <div class="news-card">
            <div class="news-header">
                <div class="tool-name">{tool_name}</div>
                <div class="news-meta"><i class="fas fa-bolt" style="color: #ffeb3b;"></i> New Update</div>
            </div>
            <div class="news-content">
                <p><strong>{summary}</strong></p>
                <p style="margin-top: 10px; font-size: 0.9em; color: #aaa;"><i class="fas fa-info-circle"></i> {why}</p>
            </div>
            <div class="news-footer">
                <a href="{url}" target="_blank" class="source-link">
                    <i class="fab fa-twitter"></i> View Post
                </a>
            </div>
        </div>
        """
        cards_html += card

    if not cards_html:
        return ""

    return f"""
    <div class="category-section">
        <h2 class="category-title">{category_title}</h2>
        {cards_html}
    </div>
    """

def build():
    print("Starting build process...")
    latest_date = get_latest_report_date()
    
    if not latest_date:
        print("No reports found.")
        return

    print(f"Latest report date: {latest_date}")
    
    report_path = os.path.join(REPORTS_DIR, latest_date)
    all_md_files = glob.glob(os.path.join(report_path, "*.md"))
    
    # Sort files to respect category order (1_Top, 2_Google...)
    all_md_files.sort()
    
    full_content_html = ""
    
    for md_file in all_md_files:
        print(f"Processing {md_file}...")
        full_content_html += parse_markdown_file(md_file)
    
    if not full_content_html:
        full_content_html = "<div class='no-news'>No significant AI news found today.</div>"

    # Fill Template
    final_html = HTML_TEMPLATE.format(
        date_str=latest_date,
        content_html=full_content_html
    )

    # Write output
    output_path = os.path.join(DOCS_DIR, "index.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"Build complete! Output: {output_path}")

if __name__ == "__main__":
    build()
