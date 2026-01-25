import os
import json
import time
import datetime
import requests

# Configuration
def load_api_key():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith("XAI_API_KEY="):
                    return line.strip().split("=")[1]
    return os.environ.get("XAI_API_KEY")

API_KEY = load_api_key()
if not API_KEY:
    raise ValueError("API Key not found. Please set XAI_API_KEY in .env file.")
MODEL = "grok-4-1-fast-non-reasoning"  # Cost-effective & fast
TARGETS_FILE = "targets.json"
BASE_REPORT_DIR = "reports"

def setup_report_dir():
    """Creates a directory for today's reports."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(BASE_REPORT_DIR, today)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def load_targets():
    """Loads the monitoring targets from JSON."""
    with open(TARGETS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_ai_news(tool_name, accounts):
    """
    Queries Grok API for the latest news about a specific tool/account.
    """
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    accounts_str = ", ".join(accounts)
    prompt = (
        f"Current Date: {current_date}. "
        f"Fetch the latest tweets from {accounts_str} in the last 3 days using x_search. "
        "FILTERING TASK: Analyze each tweet for 'Newsworthiness'. "
        "Criteria for News: New Model Releases, Feature Updates, API Changes, Strategic Announcements, or Major Policy updates. "
        "Criteria for Exclusion: Casual replies to users, single-word tweets, memes, minor maintenance, or retweets without significant added context. "
        "OUTPUT FORMAT (STRICT): "
        "If news is found, you MUST use this exact format for each item:"
        "- **Date**: YYYY-MM-DD"
        "- **URL**: https://..."
        "- **Summary**: (Concise Japanese summary)"
        "- **Why**: (Reason for importance)"
        "If NO posts pass the filter, strictly output: 'No significant news found'."
    )

    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a tech news reporter specializing in AI. usage of x_search is MANDATORY to get real-time data."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": MODEL,
        "stream": False,
        "temperature": 0
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception: {str(e)}"

def validate_url(url):
    """Checks if a URL is valid and reachable (returns 200)."""
    if "https://" not in url:
        return False
    try:
        # Fake user agent to avoid bot blocking (Twitter often blocks specific empty agents)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        r = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        return r.status_code < 400
    except:
        return False

def main():
    print("=== AI News Collection Start ===")
    report_dir = setup_report_dir()
    targets = load_targets()
    
    total_tools = sum(len(cat['tools']) for cat in targets)
    current_count = 0

    print(f"Target file: {TARGETS_FILE}")
    print(f"Report directory: {report_dir}")
    print(f"Total tools to check: {total_tools}")
    print("-" * 30)

    for category_group in targets:
        category = category_group['category']
        print(f"\nProcessing Category: {category}")
        
        # Create a combined category report file
        cat_filename = category.replace(" ", "_").replace(".", "").replace("&", "and").replace("/", "-") + ".md"
        cat_report_path = os.path.join(report_dir, cat_filename)
        
        with open(cat_report_path, 'w', encoding='utf-8') as report_file:
            report_file.write(f"# {category} - Daily Report\n\n")

            for tool in category_group['tools']:
                tool_name = tool['name']
                accounts = tool['accounts']
                current_count += 1
                
                print(f"[{current_count}/{total_tools}] Checking {tool_name} ({', '.join(accounts)})...")
                
                # Fetch news
                content = get_ai_news(tool_name, accounts)
                
                report_file.write(f"## {tool_name}\n")
                report_file.write(content + "\n\n")
                report_file.write("---\n")
                
                # Verify if '特になし' to keep logs clean
                if "No significant news" in content or "None" in content:
                    print("  -> No verified updates.")
                else:
                    print("  -> Update found!")
                
                # Sleep to avoid rate limits (politeness)
                time.sleep(2)

    print("\n=== Collection Complete ===")
    print(f"Reports saved in: {report_dir}")

if __name__ == "__main__":
    main()
