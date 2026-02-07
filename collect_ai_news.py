import os
import json
import time
import datetime
import hashlib
import requests
import threading
import subprocess
from post_to_x import post_item_to_x, get_twitter_client

# X Client (Persistent if possible)
X_CLIENT = None

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
# Use Responses API for server-side agentic x_search
API_URL = "https://api.x.ai/v1/responses"
# [IMMUTABLE] DO NOT CHANGE without user's explicit consent.
# This specific model is chosen for its non-reasoning agentic speed.
MODEL = "grok-4-1-fast-non-reasoning" 


TARGETS_FILE = "targets.json"
BASE_REPORT_DIR = "reports"

# Global lock for file writing/printing
IO_LOCK = threading.Lock()

def setup_report_dir():
    """Creates a directory for today's reports."""
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

def realtime_delivery(item):
    """
    Handles immediate delivery to X and update of the Web site.
    """
    global X_CLIENT
    with IO_LOCK:
        print(f"🚀 Real-time Delivery Initiated: {item['tool']}")
        
        # 1. Post to X
        if X_CLIENT is None:
            X_CLIENT = get_twitter_client()
        
        # Prepare item for post_to_x format (needs id)
        x_item = item.copy()
        x_item['id'] = item['url']
        
        posted = post_item_to_x(x_item, X_CLIENT)
        
        # 2. Update Web Site
        print("  🏗️ Rebuilding site...")
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            res = subprocess.run(["python", "build_site.py"], check=True, capture_output=True, text=True, encoding="utf-8", env=env)
            print("  ✅ Site rebuilt.")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Site rebuild failed: {e}")
            print(f"  STDOUT: {e.stdout}")
            print(f"  STDERR: {e.stderr}")
            return
        except Exception as e:
            print(f"  ❌ Error during site rebuild: {e}")
            return

        # 3. Git Push
        print("  ☁️ Pushing to GitHub...")
        try:
            # Stage only necessary files
            subprocess.run(["git", "add", "."], check=True)
            commit_msg = f"News Update: {item['tool']} ({datetime.datetime.now().strftime('%H:%M')})"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            
            # Pull first to avoid conflicts
            subprocess.run(["git", "pull", "--rebase"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("  🛰️ Push complete. Live at https://tadfuji.github.io/AI_TOOL_NEWS/")
        except Exception as e:
            print(f"  ⚠️ Git sync noted: {e}")

def get_category_news(category_name, tools_list):
    """
    Queries xAI Responses API with built-in x_search tool.
    The API executes X searches server-side and returns results.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    JST = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(JST)
    current_date = now.strftime("%Y-%m-%d")
    # 検索範囲を4.2時間に拡張 (4時間おきの実行に合わせる)
    from_date = (now - datetime.timedelta(hours=4.2)).strftime("%Y-%m-%dT%H:%M:%S")
    
    # Collect all X handles for this category (max 10 for x_search)
    all_accounts = []
    tools_desc = ""
    for t in tools_list:
        tools_desc += f"- {t['name']}: {', '.join(t['accounts'])}\n"
        for acc in t['accounts']:
            clean_acc = acc.lstrip('@').strip()
            if clean_acc and clean_acc not in all_accounts:
                all_accounts.append(clean_acc)
    
    # xAI x_search limit: max 10 handles per request
    allowed_handles = all_accounts[:10]
    
    # Prompt for the AI to analyze search results
    prompt = (
        f"Role: AI News Aggregator for Japanese audience.\n"
        f"Current Date: {current_date}\n\n"
        f"Task: Search X for the LATEST updates (last 2 hours) from these AI tools/companies:\n"
        f"{tools_desc}\n"
        "INSTRUCTIONS:\n"
        "1. Search X for posts from the official accounts listed above.\n"
        "2. Look for: Product launches, model updates, new features, or official announcements.\n"
        "3. Ignore: random chatter, retweets of unrelated content, promotional fluff.\n"
        "4. Output MUST be a valid JSON list. Each object represents ONE tool:\n"
        "   [\n"
        "     {\n"
        "       \"tool_name\": \"Name from the list\",\n"
        "       \"has_news\": true/false,\n"
        "       \"post_text\": \"Raw text of the post (or 'No recent updates')\",\n"
        "       \"post_date\": \"YYYY-MM-DD HH:MM\",\n"
        "       \"post_url\": \"https://x.com/...\"\n"
        "     }\n"
        "   ]\n"
        "5. If no news is found for a tool, set has_news: false.\n"
        "6. Return ONLY the JSON. No markdown fencing."
    )

    payload = {
        "model": MODEL,
        "input": [
            {"role": "user", "content": prompt}
        ],
        "tools": [
            {
                "type": "x_search",
                "allowed_x_handles": allowed_handles,
                "from_date": from_date,
                "to_date": current_date
            }
        ],
        "temperature": 0.0
    }

    try:
        for attempt in range(3):
            try:
                response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=180)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    try:
                        # Responses API: output is a list
                        # Find the 'message' type and extract text from content[].text
                        output_list = data.get('output', [])
                        text_content = ""
                        
                        for item in output_list:
                            if isinstance(item, dict) and item.get('type') == 'message':
                                content_list = item.get('content', [])
                                for content_item in content_list:
                                    if isinstance(content_item, dict) and content_item.get('type') == 'output_text':
                                        text_content = content_item.get('text', '')
                                        break
                                if text_content:
                                    break
                        
                        if not text_content:
                            return "Error: No text content in API response"

                        # Clean markdown fencing if present
                        clean_json = text_content.replace("```json", "").replace("```", "").strip()
                        return json.loads(clean_json)

                    except (KeyError, json.JSONDecodeError) as e:
                        print(f"    ⚠️ JSON Parse Error: {e}")
                        return f"Error: Parsing failed. Raw: {str(text_content)[:200]}"
                        
                elif response.status_code == 429:
                    print(f"    ⚠️ 429 Rate Limit. Sleeping 60s...")
                    time.sleep(60)
                    continue
                elif response.status_code == 500:
                    print(f"    ⚠️ 500 Server Error. Sleeping 10s and retrying...")
                    time.sleep(10)
                    continue
                else:
                    return f"Error: {response.status_code} - {response.text[:500]}"
            except requests.exceptions.Timeout:
                print(f"    ⚠️ Request timed out (attempt {attempt+1}/3), retrying...")
                continue
        return "Error: Failed after 3 retries"

    except Exception as e:
        return f"Exception: {str(e)}"


def process_category(category_data, report_dir):
    """Worker function for Category Batch execution."""
    
    cat_name = category_data['category']
    tools_list = category_data['tools']
    JST = datetime.timezone(datetime.timedelta(hours=9))
    
    with IO_LOCK:
        print(f"📦 Batch Processing: {cat_name} ({len(tools_list)} tools)...")
    
    try:
        results = get_category_news(cat_name, tools_list)
        
        if isinstance(results, str) and results.startswith("Error"):
             with IO_LOCK:
                 print(f"  ❌ Batch Failed: {cat_name} -> {results}")
             return

        if not isinstance(results, list):
             with IO_LOCK:
                 print(f"  ❌ Batch Error: Expected list, got {type(results)}")
             return

        for item in results:
            tool_name = item.get('tool_name', 'Unknown')
            has_news = item.get('has_news', False)
            
            if not has_news:
                with IO_LOCK:
                    print(f"  ⚪ {tool_name}: No news.")
                continue

            post_text = item.get('post_text', '')
            post_date = item.get('post_date', 'Unknown Date')
            post_url = item.get('post_url', '#')

            final_summary = post_text
            final_why = "詳細をご確認ください。"
            final_score = 3
            
            # 1. 投稿URLからユニークなファイル名を生成
            url_hash = hashlib.md5(post_url.encode()).hexdigest()[:8]
            count_str = tool_name.replace(' ', '_').replace('/', '-')
            filename = f"{count_str}_{url_hash}.json"
            filepath = os.path.join(report_dir, filename)

            # 2. 既にアーカイブ済みの場合はGeminiを呼ばずにスキップ（重要：コスト削減）
            if os.path.exists(filepath):
                with IO_LOCK:
                    print(f"  ⏭️ {tool_name}: Already processed. Skipping Gemini.")
                continue

            if len(post_text) > 15:
                try:
                    from gemini_x_filter import filter_x_updates_with_gemini
                    gemini_result = filter_x_updates_with_gemini(post_text, tool_name)
                    
                    if gemini_result is None:
                        # 有用なニュースと判定されなかった場合
                        continue
                    
                    if "error" in gemini_result:
                        with IO_LOCK:
                            print(f"  ⚠️ Gemini Skip: {gemini_result['error']}")
                        final_summary = post_text
                    else:
                        final_summary = gemini_result.get('summary', post_text)
                        final_why = gemini_result.get('why', final_why)
                        final_score = gemini_result.get('score', 3)
                except ImportError:
                    pass
            else:
                # 短すぎる投稿はニュースではないため除外
                with IO_LOCK:
                    print(f"  ⚪ {tool_name}: Post too short ({len(post_text)} chars). Skipping.")
                continue

            with IO_LOCK:
                print(f"  ✅ News Found: {tool_name}")

            # 3. JSONレポートの保存
            
            # Improvement: Save as structured JSON instead of Markdown (Data Integrity)
            report_data = {
                "category": cat_name,
                "tool": tool_name,
                "summary": final_summary,
                "why": final_why,
                "score": final_score,
                "post_date": post_date,
                "url": post_url,
                "collected_at": datetime.datetime.now(JST).isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            # 4. Real-time Delivery (Web & X)
            realtime_delivery(report_data)

    except Exception as e:
        with IO_LOCK:
            print(f"  🔥 Batch Critical Failure {cat_name}: {e}")
            
    time.sleep(15) 

# Main Execution Block
if __name__ == "__main__":
    print("=== AI News Collection Start (Responses API Mode) ===")
    
    report_dir = setup_report_dir()
    config = load_targets()
    
    print(f"🚀 Launching {len(config)} category agents...")

    # Process categories sequentially to strictly avoid rate limits
    for cat in config:
        try:
            process_category(cat, report_dir)
        except Exception as exc:
            print(f"Category exception: {exc}")

    print("\n=== Collection Complete ===")
