import shutil
import os

SOURCE_DIR = r"C:\Users\tadah\Desktop\Antigravity\AI_TOOL_NEWS"
TARGET_DIR = r"C:\Users\tadah\Desktop\Antigravity\ai-news-bot"

FILES_TO_SYNC = [
    "app.py",
    "collect_rss_gemini.py",
    "rss_client.py",
    "ai_client.py",
    "grok_poster.py",
    "monitor_models.py",
    "check_models.py",
    "collect_ai_news.py",  # Ensure X patrol script is there too
    ".env" # Sync keys
]

WORKFLOWS_TO_SYNC = [
    ".github/workflows/daily_rss_gemini.yml",
    ".github/workflows/hourly_x_patrol.yml",
    ".github/workflows/model_monitor.yml"
]

def sync_files():
    print(f"🚀 Starting Sync: {SOURCE_DIR} -> {TARGET_DIR}")
    
    # Sync Root Files
    for file in FILES_TO_SYNC:
        src = os.path.join(SOURCE_DIR, file)
        dst = os.path.join(TARGET_DIR, file)
        
        if os.path.exists(src):
            try:
                shutil.copy2(src, dst)
                print(f"✅ Copied: {file}")
            except Exception as e:
                print(f"❌ Failed to copy {file}: {e}")
        else:
            print(f"⚠️ Source missing: {file}")

    # Sync Workflows
    os.makedirs(os.path.join(TARGET_DIR, ".github", "workflows"), exist_ok=True)
    for wf in WORKFLOWS_TO_SYNC:
        src = os.path.join(SOURCE_DIR, wf)
        dst = os.path.join(TARGET_DIR, wf)
        
        # Determine filename from path
        filename = os.path.basename(wf)
        
        if os.path.exists(src):
            try:
                shutil.copy2(src, dst)
                print(f"✅ Copied Workflow: {filename}")
            except Exception as e:
                print(f"❌ Failed to copy workflow {filename}: {e}")
        else:
            print(f"⚠️ Source workflow missing: {wf}")

    # Remove old main.py to avoid confusion if needed, but safer to keep for now.
    # print("🧹 Cleanup complete.")

if __name__ == "__main__":
    sync_files()
