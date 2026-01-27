"""
翻訳スクリプト v2: 英語レポートを日本語に変換
全ての形式に対応した改良版
"""
import os
import re
import glob
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

def is_likely_english(text: str) -> bool:
    """Check if the text is likely English (and not already translated)."""
    # Skip if already has Japanese summary format
    if "**Summary**:" in text and "集" in text:  # Has Japanese characters
        return False
    # Check for English word patterns
    english_patterns = [
        r'\bthe\b', r'\bis\b', r'\bare\b', r'\bwith\b', r'\bfor\b',
        r'\bnow\b', r'\bcan\b', r'\byou\b', r'\bour\b', r'\bwe\b',
        r'\bthis\b', r'\bthat\b', r'\bhave\b', r'\bhas\b',
        r'\bwill\b', r'\bjust\b', r'\bnew\b', r'\bget\b',
        r'\bbeen\b', r'\bwere\b', r'\bfrom\b', r'\bmore\b'
    ]
    matches = sum(1 for p in english_patterns if re.search(p, text.lower()))
    # If more than 2 English words and few Japanese chars
    japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text))
    return matches >= 2 and japanese_chars < 10

def translate_to_japanese(post_text: str, tool_name: str) -> str:
    """Translate English post to Japanese summary format using Gemini."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found")
        return None
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
あなたはAIツールニュースの翻訳者です。以下の英語の投稿を日本語に翻訳してください。

ツール名: {tool_name}
英語投稿:
\"\"\"
{post_text}
\"\"\"

出力形式（厳守）:
- **Summary**: わかりやすい日本語で説明（150文字以内、です/ます調）
- **Why**: ユーザーにとってのメリット（100文字以内、親しみやすい表現）

ルール:
- 技術用語は必要に応じて括弧内に説明を追加
- 温かく親しみやすい言葉遣いを使用
- ユーザーの実用的なメリットに焦点を当てる
- SummaryとWhyの2行のみを出力

出力例:
- **Summary**: Claudeが新しく○○機能に対応しました。これにより、△△ができるようになります。
- **Why**: □□の作業が楽になり、毎日の効率がアップします。
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def process_report_file(filepath: str) -> bool:
    """Process a single report file and translate English posts."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Extract tool name from file path
    tool_name = os.path.splitext(os.path.basename(filepath))[0].replace('_', ' ')
    
    # Find all sections starting with "- Post:"
    # Pattern: "- Post: <text until next '- Time:' or '- Post:'>"
    lines = content.split('\n')
    new_lines = []
    i = 0
    modified = False
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a Post line
        if line.strip().startswith('- Post:'):
            post_content = line[line.find('- Post:') + 7:].strip()
            j = i + 1
            
            # Collect multiline post content (until we hit Time, URL, or another Post)
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line.startswith('- Time:') or next_line.startswith('- URL:') or next_line.startswith('- Post:'):
                    break
                if next_line and not next_line.startswith('#'):
                    post_content += " " + next_line
                j += 1
            
            post_content = post_content.strip()
            
            # Check if this needs translation
            if post_content and is_likely_english(post_content):
                print(f"  Translating: {post_content[:50]}...")
                translated = translate_to_japanese(post_content, tool_name)
                time.sleep(0.5)  # Rate limiting
                
                if translated:
                    new_lines.append(f'- Post: {translated}')
                    modified = True
                    # Skip original content lines, but keep Time and URL
                    i = j
                    continue
            
            # If no translation needed, keep original lines
            while i < j:
                new_lines.append(lines[i])
                i += 1
            continue
        else:
            new_lines.append(line)
        
        i += 1
    
    if modified:
        new_content = '\n'.join(new_lines)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    print("=== 英語レポート翻訳開始 (v2) ===\n")
    
    # Find all report files
    report_files = glob.glob(os.path.join(REPORTS_DIR, "*", "*.md"))
    
    translated_count = 0
    for filepath in sorted(report_files):
        print(f"Processing: {os.path.basename(filepath)}")
        if process_report_file(filepath):
            translated_count += 1
            print(f"  ✓ 翻訳完了")
        else:
            print(f"  - スキップ (翻訳不要)")
    
    print(f"\n=== 完了: {translated_count} ファイル翻訳 ===")

if __name__ == "__main__":
    main()
