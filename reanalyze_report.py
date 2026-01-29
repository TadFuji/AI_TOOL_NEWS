import json
import os
from gemini_x_filter import filter_x_updates_with_gemini

# 対象のファイルパス
target_file = r"c:\Users\tadah\Desktop\Antigravity\AI_TOOL_NEWS\reports\2026-01-29\xAI_26899158.json"

def reanalyze():
    if not os.path.exists(target_file):
        print(f"File not found: {target_file}")
        return

    print(f"--- Re-analyzing {os.path.basename(target_file)} ---")
    
    with open(target_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 現在のsummary（混在テキスト）をソースとして使用
    source_text = data.get("summary", "")
    tool_name = data.get("tool", "Unknown")

    print(f"Original summary (mixed data):\n{source_text[:100]}...\n")

    # 新しいロジックで再分析
    result = filter_x_updates_with_gemini(source_text, tool_name)

    if result and "error" not in result:
        print("✅ Analysis Success!")
        print(f"NEW Summary: {result['summary']}")
        print(f"NEW Why: {result['why']}")
        print(f"NEW Score: {result['score']}")

        # データを更新
        data["summary"] = result["summary"]
        data["why"] = result["why"]
        data["score"] = result["score"]

        # ファイルに書き戻し
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("\n--- JSON file updated successfully. ---")
    else:
        print(f"❌ Analysis failed: {result}")

if __name__ == "__main__":
    reanalyze()
