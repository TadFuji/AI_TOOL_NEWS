"""
翻訳スクリプト: 英語レポートを日本語に変換
既存のマークダウン形式を維持しながら、英語の投稿テキストを日本語サマリーに変換する
"""
import os
import re
import glob
from google import genai
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

def is_english_post(text: str) -> bool:
    """Check if the post text is mostly English (needs translation)."""
    # If it already has Japanese summary format, skip
    if "**Summary**:" in text or "**Why**:" in text:
        return False
    # Check for English patterns
    english_patterns = [
        r'\bthe\b', r'\bis\b', r'\bare\b', r'\bwith\b', r'\bfor\b',
        r'\bnow\b', r'\bcan\b', r'\byou\b', r'\bour\b', r'\bwe\b'
    ]
    matches = sum(1 for p in english_patterns if re.search(p, text.lower()))
    return matches >= 2

def translate_post_to_japanese(post_text: str, tool_name: str) -> str:
    """Translate English post to Japanese summary format using Gemini."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found")
        return None
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
Role: AI Tool Update Translator for Japanese Audience

Task: Translate and summarize the following English post about "{tool_name}" into Japanese.

English Post:
\"\"\"
{post_text}
\"\"\"

OUTPUT FORMAT (Mandatory):
1. **Summary**: Write a clear, kind, and easy-to-understand Japanese explanation (~150 chars max). Use Desu/Masu polite form. Explain what this update means for users.
2. **Why**: Explain why this matters to users in a friendly tone (~100 chars max).

RULES:
- Keep technical terms but add Japanese explanation in parentheses if needed
- Use warm, approachable language (優しい表現)
- Focus on practical user benefits
- Output ONLY the Summary and Why lines, nothing else

Example output:
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
    
    # Parse posts: "- Post: <text>" followed by "- Time:" and "- URL:"
    # Pattern to find English posts that need translation
    post_pattern = re.compile(
        r'(- Post: )([^\n]+(?:\n(?!- Time:|- URL:)[^\n]+)*)\n(- Time: [^\n]+)\n(- URL: [^\n]+)',
        re.MULTILINE
    )
    
    # Extract tool name from file path
    tool_name = os.path.splitext(os.path.basename(filepath))[0].replace('_', ' ')
    
    def translate_match(match):
        prefix = match.group(1)
        post_text = match.group(2).strip()
        time_line = match.group(3)
        url_line = match.group(4)
        
        if not is_english_post(post_text):
            return match.group(0)  # Return unchanged
        
        print(f"  Translating: {post_text[:50]}...")
        translated = translate_post_to_japanese(post_text, tool_name)
        
        if translated:
            # Format the new entry
            new_entry = f"- Post: {translated}\n{time_line}\n{url_line}"
            return new_entry
        else:
            return match.group(0)  # Keep original on error
    
    new_content = post_pattern.sub(translate_match, content)
    
    if new_content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    print("=== 英語レポート翻訳開始 ===\n")
    
    # Find all report files
    report_files = glob.glob(os.path.join(REPORTS_DIR, "*", "*.md"))
    
    translated_count = 0
    for filepath in sorted(report_files):
        print(f"Processing: {os.path.basename(filepath)}")
        if process_report_file(filepath):
            translated_count += 1
            print(f"  ✓ 翻訳完了")
        else:
            print(f"  - スキップ (日本語済み or 英語なし)")
    
    print(f"\n=== 完了: {translated_count} ファイル翻訳 ===")

if __name__ == "__main__":
    main()
