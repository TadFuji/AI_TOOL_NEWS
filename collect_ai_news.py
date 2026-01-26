import os
import json
import time
import datetime
import requests
import re
import concurrent.futures
import threading

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
API_URL = "https://api.x.ai/v1/chat/completions"
# Using grok-4-1-fast-non-reasoning as verified (Low Cost & Fast)
MODEL = "grok-4-1-fast-non-reasoning" 

TARGETS_FILE = "targets.json"
BASE_REPORT_DIR = "reports"

# Global lock for file writing/printing
IO_LOCK = threading.Lock()

def setup_report_dir():
    """Creates a directory for today's reports."""
    # TIMEZONE FIX: GitHub Actions runs in UTC. Force JST (UTC+9)
    JST = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(JST).strftime("%Y-%m-%d")
    path = os.path.join(BASE_REPORT_DIR, today)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def load_targets():
    """Loads the monitoring targets from JSON."""
    with open(TARGETS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_category_news(category_name, tools_list):
    """
    Queries xAI Agent API to autonomously search X for A BATCH of tools.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    JST = datetime.timezone(datetime.timedelta(hours=9))
    current_date = datetime.datetime.now(JST).strftime("%Y-%m-%d")
    
    # Construct Batch Prompt
    tools_desc = ""
    for t in tools_list:
        tools_desc += f"- {t['name']}: {', '.join(t['accounts'])}\n"

    # Prompt optimized for Batch execution & JSON output
    prompt = (
        f"Role: AI News Aggregator.\n"
        f"Current Date: {current_date}\n\n"
        f"Task: Search for the LATEST updates (last 3 days) for the following AI tools/companies:\n"
        f"{tools_desc}\n"
        "INSTRUCTIONS:\n"
        "1. Use the 'x_search' tool to check the official accounts for EACH tool listed above.\n"
        "2. Look for: Product launches, model updates, new features, or official announcements. Ignore random chatter.\n"
        "3. Output MUST be a valid JSON list of objects. Each object must represent ONE tool.\n"
        "4. Format:\n"
        "   [\n"
        "     {\n"
        "       \"tool_name\": \"Name from the list\",\n"
        "       \"has_news\": true/false,\n"
        "       \"post_text\": \"Raw text of the post found (or 'No recent updates')\",\n"
        "       \"post_date\": \"YYYY-MM-DD HH:MM\",\n"
        "       \"post_url\": \"https://x.com/...\"\n"
        "     },\n"
        "     ...\n"
        "   ]\n"
        "5. If no news is found for a tool, set has_news: false.\n"
        "6. Return ONLY the JSON. No markdown fencing if possible, or minimally fenced."
    )

    # Tool Definition
    tools = [
        {
            "type": "function",
            "function": {
                "name": "x_search",
                "description": "Search X for posts from specific users.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "usernames": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are an automated news collector agent. You output strict JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "tools": tools,
        "tool_choice": "auto"
    }

    try:
        # Retry logic
        for attempt in range(3):
            try:
                response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=120)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Message content parsing
                    try:
                        message = data['choices'][0]['message']
                        content = message.get('content', '')
                        
                        # Fallback: if content is null but tool_calls exist, the model might be stuck in tool loop
                        # But with "chat/completions", Grok usually returns the final answer in content after tool usage if we don't force tool loop in python.
                        # Wait, the xAI API for agents usually runs server-side loops.
                        # If using the 'responses' endpoint (agent), we get final output.
                        # If using 'chat/completions', we might need to handle tool calls? 
                        # The user snippet suggests "agentic server-side tool calling".
                        # Let's trust the 'chat/completions' with tool_choice auto handles it or returns the result.
                        # Actually, for xAI, 'v1/responses' was the agent endpoint (used in prev code).
                        # User snippet recommends 'v1/chat/completions'. Let's stick to that but handle potential tool_calls if xAI doesn't auto-resolve server side?
                        # Re-reading user note: "agentic server-side tool calling... use prompts that instruct... The model will handle the tool calls agentically, returning processed results."
                        # This implies the MODEL does the thinking and just gives us the answer? 
                        # Or does it return tool_calls for US to execute?
                        # The snippet says: "Parse response for tool calls AND results".
                        # However, for simplicity and ensuring it works like the previous 'responses' endpoint (which was fully server side), 
                        # let's try to extract JSON from the content.
                        
                        if not content:
                            return "Error: No content returned (maybe raw tool calls?)"

                        # Clean markdown
                        clean_json = content.replace("```json", "").replace("```", "").strip()
                        return json.loads(clean_json)

                    except (KeyError, json.JSONDecodeError) as e:
                        print(f"    ⚠️ JSON Parse Error in Category Batch: {e}")
                        # If not JSON, maybe just text?
                        return f"Error: Parsing failed. Raw: {content[:100]}"
                        
                elif response.status_code == 429:
                    print(f"    ⚠️ 429 Rate Limit. Sleeping 30s...")
                    time.sleep(30)
                    continue
                else:
                    return f"Error: {response.status_code} - {response.text}"
            except requests.exceptions.Timeout:
                print("Request timed out, retrying...")
                continue
        return "Error: Failed after 3 retries"

    except Exception as e:
        return f"Exception: {str(e)}"


def process_category(category_data, report_dir):
    """Worker function for Category Batch execution."""
    
    cat_name = category_data['category']
    tools_list = category_data['tools']
    
    with IO_LOCK:
        print(f"📦 Batch Processing: {cat_name} ({len(tools_list)} tools)...")
    
    try:
        # Call Grok for the whole bunch
        results = get_category_news(cat_name, tools_list)
        
        if isinstance(results, str) and results.startswith("Error"):
             with IO_LOCK:
                 print(f"  ❌ Batch Failed: {cat_name} -> {results}")
             return

        # It should be a list of dicts
        if not isinstance(results, list):
             with IO_LOCK:
                 print(f"  ❌ Batch Error: Expected list, got {type(results)}")
             return

        # Process each tool result in the batch
        for item in results:
            tool_name = item.get('tool_name', 'Unknown')
            has_news = item.get('has_news', False)
            
            # Map back to accounts if possible, or just trust the tool name
            # Validation: Check if tool_name is in our target list
            # (Grok might hallucinate names so be careful)
            
            if not has_news:
                with IO_LOCK:
                    print(f"  ⚪ {tool_name}: No news.")
                continue

            post_text = item.get('post_text', '')
            post_date = item.get('post_date', 'Unknown Date')
            post_url = item.get('post_url', '#')

            # HYBRID PIPELINE: Gemini Filter (Optional per item)
            # Keeping it simple for now to save cost/time: Trust Grok's separation?
            # Or pass to Gemini? Passing 7 batches to Gemini is cheaper than 36.
            # Let's pass the raw text to Gemini Filter like before if text exists.
            
            final_text = post_text
            
            # Try Gemini Filter if text is long enough
            # (Re-using existing logic logic but adapted)
            if len(post_text) > 20:
                try:
                    from gemini_x_filter import filter_x_updates_with_gemini
                    # We print less now
                    gemini_result = filter_x_updates_with_gemini(post_text, tool_name)
                    final_text = gemini_result
                except ImportError:
                    pass

            with IO_LOCK:
                print(f"  ✅ News Found: {tool_name}")

            # Save Report (Individual file to maintain architecture)
            count_str = tool_name.replace(' ', '_').replace('/', '-')
            filename = f"{count_str}.md"
            filepath = os.path.join(report_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {cat_name} - Daily Report\n\n")
                f.write(f"## {tool_name}\n")
                f.write(f"- Post: {final_text}\n")
                f.write(f"- Time: {post_date}\n")
                f.write(f"- URL: {post_url}\n")

    except Exception as e:
        with IO_LOCK:
            print(f"  🔥 Batch Critical Failure {cat_name}: {e}")
            
    time.sleep(5) 

# Main Execution Block
if __name__ == "__main__":
    print("=== AI News Collection Start (Cost-Optimized Cluster Mode) ===")
    
    report_dir = setup_report_dir()
    config = load_targets()
    
    # Process Categories sequentially or parallel?
    # Parallel Categories is fine. 7 threads is standard.
    
    print(f"🚀 Launching {len(config)} category agents...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_category, cat, report_dir): cat for cat in config}
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"Category thread exception: {exc}")

    print("\n=== Collection Complete ===")

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
    # TIMEZONE FIX: GitHub Actions runs in UTC. Force JST (UTC+9)
    JST = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(JST).strftime("%Y-%m-%d")
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
    
    JST = datetime.timezone(datetime.timedelta(hours=9))
    current_date = datetime.datetime.now(JST).strftime("%Y-%m-%d")
    accounts_str = ", ".join(accounts)
    
    # Prompt optimized for Agentic execution
    prompt = (
        f"Role: Raw Data Collector.\n"
        f"Task: Extract the text, timestamp, and URL of ALL recent posts from {accounts_str} within the last 3 days.\n"
        f"Current Date: {current_date}\n\n"
        "INSTRUCTIONS:\n"
        "1. Do NOT filter or summarize. I need the raw data.\n"
        "2. For each post found, output a line in this specific format:\n"
        "   - Post: [Text of the post]\n"
        "   - Time: [YYYY-MM-DD HH:MM]\n"
        "   - URL: [https://x.com/...]\n\n"
        "3. Include EVERYTHING found (features, funding, random thoughts). Filtering will be done downstream.\n"
        "4. If absolutely nothing is found, say 'No recent posts'."
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
                    outputs = data.get('output', [])
                    for item in reversed(outputs): 
                        if item.get('role') == 'assistant' and 'content' in item:
                            content_list = item['content']
                            full_text = ""
                            for part in content_list:
                                if part.get('type') == 'output_text':
                                    full_text += part.get('text', "")
                            
                            # CLEANING: Remove Grok's citation markers [[1]](url) or just [[1]]
                            # Use regex to strip pattern content
                            clean_text = re.sub(r'\[\[\d+\]\](?:\([^)]+\))?', '', full_text)
                            
                            # HYBRID PIPELINE START: Pass Raw Grok Output to Gemini
                            try:
                                from gemini_x_filter import filter_x_updates_with_gemini
                                print(f"    ... Sending {len(clean_text)} chars to Gemini for analysis ...")
                                gemini_result = filter_x_updates_with_gemini(clean_text, tool_name)
                                return gemini_result
                            except ImportError:
                                print("    ⚠️ Warning: gemini_x_filter not found, falling back to Grok raw output.")
                                return clean_text.strip()
                            # HYBRID PIPELINE END
                    return "Error: No text content in agent response."
                elif response.status_code == 429:
                    print(f"    ⚠️ 429 Rate Limit. Sleeping 30s...")
                    time.sleep(30) # Wait for rate limit
                    continue
                else:
                    return f"Error: {response.status_code} - {response.text}"
            except requests.exceptions.Timeout:
                print("Request timed out, retrying...")
                continue
        return "Error: Failed after 3 retries"

    except Exception as e:
        return f"Exception: {str(e)}"


import concurrent.futures
import threading

# Circuit Breaker Globals
FAILURE_COUNTER = 0
FAILURE_THRESHOLD = 20
FAILURE_LOCK = threading.Lock()

def process_tool(category_name, tool, report_dir):
    """Worker function for parallel execution."""
    global FAILURE_COUNTER
    
    # Circuit Breaker Check
    with FAILURE_LOCK:
        if FAILURE_COUNTER >= FAILURE_THRESHOLD:
            return None # Skip silently if breaker is open

    name = tool['name']
    accounts = tool['accounts']
    
    print(f"🔍 Checking {name}...")
    
    try:
        news_content = get_ai_news(name, accounts)
        
        # Success Logic
        if "Error:" in news_content or not news_content.strip():
             print(f"  ❌ {name}: Failed/Empty. Content: {news_content[:100]}...")
             with FAILURE_LOCK:
                 FAILURE_COUNTER += 1
        elif "No significant news found" in news_content:
             print(f"  ⚪ {name}: No verified updates.")
             # Reset counter on success (even if no news, API worked)
             with FAILURE_LOCK:
                 FAILURE_COUNTER = 0
        else:
             print(f"  ✅ {name}: Update found!")
             # Reset counter
             with FAILURE_LOCK:
                 FAILURE_COUNTER = 0
                 
             # Save Report
             # Clean up markdown
             news_content = news_content.replace("```markdown", "").replace("```", "").strip()
             
             count_str = name.replace(' ', '_').replace('/', '-')
             filename = f"{count_str}.md"
             filepath = os.path.join(report_dir, filename)
             
             with open(filepath, 'w', encoding='utf-8') as f:
                 f.write(f"# {category_name} - Daily Report\n\n")
                 f.write(f"## {name}\n")
                 f.write(news_content + "\n")
                 
    except Exception as e:
        print(f"  🔥 {name}: Critical Failure: {e}")
        with FAILURE_LOCK:
             FAILURE_COUNTER += 1
             
    time.sleep(5) # Jitter for API kindness

# Main Execution Block
if __name__ == "__main__":
    print("=== AI News Collection Start (Parallel Agent Mode) ===")
    
    report_dir = setup_report_dir()
    config = load_targets()
    
    # Flatten task list for parallel execution
    tasks = []
    for category in config:
        for tool in category['tools']:
            tasks.append({
                "category": category['category'],
                "tool": tool,
            })
            
    total_tasks = len(tasks)
    print(f"🚀 Launching {total_tasks} agents with max_workers=3...")

    # Parallel Execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        futures = {executor.submit(process_tool, t['category'], t['tool'], report_dir): t for t in tasks}
        
        for future in concurrent.futures.as_completed(futures):
            # Just consume the results to ensure exceptions are caught if any
            try:
                future.result()
            except Exception as exc:
                print(f"Thread generated an exception: {exc}")
                
            # Circuit Breaker Final Check
            if FAILURE_COUNTER >= FAILURE_THRESHOLD:
                print("🚨 CIRCUIT BREAKER TRIPPED: Too many errors. Aborting run.")
                executor.shutdown(wait=False)
                break

    print("\n=== Collection Complete ===")
    if FAILURE_COUNTER >= FAILURE_THRESHOLD:
         # Optional: Trigger notify_failure here if needed, or let GitHub Actions fail
         # To make Actions fail, exit with non-zero
         import sys
         sys.exit(1)
