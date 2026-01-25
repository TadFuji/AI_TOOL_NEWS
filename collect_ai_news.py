import os
import json
import time
import datetime
import requests
import re

# Configuration
def load_api_key():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("XAI_API_KEY="):
                    return line.strip().split("=")[1]
    return os.environ.get("XAI_API_KEY")

API_KEY = load_api_key()
# Crucial: Use Agent Endpoint and Grok-4 family for server-side x_search
API_URL = "https://api.x.ai/v1/responses"
MODEL = "grok-4-1-fast-non-reasoning" 

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
    Queries xAI Agent API to autonomously search X and report news.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    accounts_str = ", ".join(accounts)
    
    # Prompt optimized for Agentic execution
    prompt = (
        f"Role: Expert AI News Reporter using real-time X data.\n"
        f"Task: Search for the LATEST significant updates from {accounts_str} within the last 24 hours.\n"
        f"Current Date: {current_date}\n\n"
        "STEPS:\n"
        "1. USE x_search to find posts from these accounts.\n"
        "2. FILTER for: New Models, Feature Launches, API Updates, or Strategic Partnerships.\n"
        "3. IGNORE: Replies, memes, maintenance, or generic hype.\n"
        "4. OUTPUT: If valid news is found, output in this format:\n"
        "- **Date**: YYYY-MM-DD\n"
        "- **URL**: (The specific tweet URL found via search)\n"
        "- **Summary**: (Concise Japanese summary)\n"
        "- **Why**: (Impact analysis)\n"
        "If NO significant news is found, output exactly: 'No significant news found'."
    )

    # Native Tool Definition for Server-Side Execution
    tools = [{"type": "x_search"}]

    payload = {
        "input": prompt,
        "model": MODEL,
        "stream": False,
        "temperature": 0.0,
        "tools": tools,
        "tool_choice": "auto"
    }

    try:
        # Retry logic for stability
        for attempt in range(3):
            try:
                response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    # Parse specific /v1/responses format
                    # Content is deeply nested in output -> assistant message -> content -> text
                    outputs = data.get('output', [])
                    for item in reversed(outputs): # Look for the final answer
                        if item.get('role') == 'assistant' and 'content' in item:
                            content_list = item['content']
                            # Combine all text parts
                            full_text = ""
                            for part in content_list:
                                if part.get('type') == 'output_text':
                                    full_text += part.get('text', "")
                            return full_text
                    return "Error: No text content in agent response."
                elif response.status_code == 429:
                    time.sleep(5) # Wait for rate limit
                    continue
                else:
                    return f"Error: {response.status_code} - {response.text}"
            except requests.exceptions.Timeout:
                print("Request timed out, retrying...")
                continue
        return "Error: Failed after 3 retries"

    except Exception as e:
        return f"Exception: {str(e)}"


# Main Execution Block
if __name__ == "__main__":
    print("=== AI News Collection Start (Agent Mode) ===")
    print(f"Target file: {TARGETS_FILE}")
    
    report_dir = setup_report_dir()
    print(f"Report directory: {report_dir}")
    
    config = load_targets()
    
    # Calculate total tasks
    total_tools = sum(len(cat['tools']) for cat in config)
    print(f"Total tools to check: {total_tools}")
    print("-" * 30)

    count = 0
    for category in config:
        cat_name = category['category']
        print(f"\nProcessing Category: {cat_name}")
        
        for tool in category['tools']:
            count += 1
            name = tool['name']
            accounts = tool['accounts']
            
            print(f"[{count}/{total_tools}] Checking {name} ({', '.join(accounts)})...")
            
            # --- AGENT EXECUTION ---
            try:
                news_content = get_ai_news(name, accounts)
                
                # Verify content - if it's just an error or empty, treat as no news
                if "Error:" in news_content or not news_content.strip():
                     print(f"  -> Failed/Empty: {news_content[:50]}...")
                elif "No significant news found" in news_content:
                    print("  -> No verified updates.")
                else:
                    # Clean up markdown code blocks if present
                    news_content = news_content.replace("```markdown", "").replace("```", "").strip()
                    
                    if "**Date**:" in news_content:
                        print("  -> Update found!")
                        # Save Report
                        filename = f"{count}_{name.replace(' ', '_').replace('/', '-')}.md"
                        filepath = os.path.join(report_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(f"# {cat_name} - Daily Report\n\n")
                            f.write(f"## {name}\n")
                            f.write(news_content + "\n")
                    else:
                         print("  -> Output format mismatch (ignoring).")

            except Exception as e:
                print(f"  -> Critical Failure: {e}")
            
            # Gentle pacing to avoid hitting rate limits
            time.sleep(2)

    print("\n=== Collection Complete ===")
    print(f"Reports saved in: {report_dir}")
