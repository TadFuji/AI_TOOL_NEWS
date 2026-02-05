import json
import os
import datetime
from collect_ai_news import realtime_delivery

def test():
    # Mock item
    item = {
        "category": "Test Category",
        "tool": "Antigravity News Bot",
        "summary": "【テスト配信】リアルタイム配信機能のデプロイが完了しました。現在、各AIツールからの情報を自動検知し、即座にXとWebサイトへ公開するシステムが稼働中です。",
        "why": "ニュースの鮮度を最優先し、情報収集から公開までのタイムラグを極限まで短縮するためです。",
        "score": 4,
        "post_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "url": "https://github.com/TadFuji/AI_TOOL_NEWS", # Dummy URL
        "collected_at": datetime.datetime.now().isoformat()
    }
    
    print("Starting test delivery...")
    
    # Save to reports folder so builder picks it up
    JST = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(JST).strftime("%Y-%m-%d")
    report_dir = os.path.join("reports", today)
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    filepath = os.path.join(report_dir, "test_item.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(item, f, ensure_ascii=False, indent=2)

    realtime_delivery(item)
    print("Test delivery complete.")

if __name__ == "__main__":
    test()
