import json
import os
import glob
import time
from gemini_x_filter import filter_x_updates_with_gemini

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

def batch_reanalyze():
    # 全てのJSONレポートを取得
    json_files = glob.glob(os.path.join(REPORTS_DIR, "*", "*.json"))
    total = len(json_files)
    
    print(f"🚀 Found {total} reports. Starting batch re-analysis...")
    
    count = 0
    updated = 0
    
    for filepath in json_files:
        count += 1
        filename = os.path.basename(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"  [{count}/{total}] ⚠️ Skip {filename}: Read Error {e}")
                continue

        # すでに処理済みのものはスキップ（scoreがあり、summaryが以前の混在形式でない場合）
        # ただし、今回は「一括リフレッシュ」なので、whyがデフォルト値（Check details / 詳細をご確認ください）のもの、
        # またはscoreがないものを対象にします。
        is_legacy = "score" not in data or "詳細をご確認ください" in data.get("why", "") or "Check details" in data.get("why", "")
        
        if not is_legacy:
            # print(f"  [{count}/{total}] ✅ Already up-to-date: {filename}")
            continue

        print(f"  [{count}/{total}] 🔍 Analyzing: {filename}...")
        
        # 以前のまとめテキスト（混在データ）をソースにする
        source_text = data.get("summary", "")
        tool_name = data.get("tool", "Unknown")
        
        # 新ロジックで再分析
        try:
            result = filter_x_updates_with_gemini(source_text, tool_name)
            
            if result and "error" not in result:
                data["summary"] = result["summary"]
                data["why"] = result["why"]
                data["score"] = result["score"]
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                updated += 1
                print(f"    ✨ Updated! [Score: {result['score']}]")
            else:
                print(f"    ⚠️ Failed or No News: {result}")
        except Exception as e:
            print(f"    🔥 Error during Gemini call: {e}")
        
        # APIレート制限への配慮（短時間なら不要な場合が多いですが、安全のため少し待機）
        time.sleep(1)

    print(f"\n=== Batch Processing Complete ===")
    print(f"Checked: {total} files")
    print(f"Updated: {updated} files")

if __name__ == "__main__":
    batch_reanalyze()
