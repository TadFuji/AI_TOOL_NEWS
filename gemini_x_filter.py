import os
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

def filter_x_updates_with_gemini(raw_text: str, tool_name: str) -> dict:
    """
    Filters and summarizes X updates using Gemini 3 Flash Preview.
    Returns a dictionary with 'summary' and 'why', or None if no news found.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_API_KEY not found."}

    client = genai.Client(api_key=api_key)

    prompt = f"""
Role: Expert AI Tool Analyst & Translator.
Task: Analyze the following raw search results from X (formerly Twitter) about the AI tool "{tool_name}".
Determine if there are any **FUNCTIONAL UPDATES** (New Features, Bug Fixes, Version Releases, Performance Improvements).

Raw Search Results:
\"\"\"
{raw_text}
\"\"\"

CRITERIA (Strictly Enforced):
1. **INCLUDE**: 
   - New capabilities (e.g., "Now you can upload PDFs")
   - Model updates (e.g., "v2.0 released")
   - Bug fixes or performance boosts
   - Service status (e.g., "Outages resolved")
2. **EXCLUDE (Noise)**:
   - Funding/Financial news, corporate partnerships, hiring, generic marketing, or user opinions.

OUTPUT FORMAT (STRICT JSON ONLY):
If valid functional news is found, return a JSON object with exactly three keys:
1. "summary": A clear, polite summary in GENTLE, POLITE JAPANESE (Desu/Masu tone). ~150 characters.
2. "why": A technical insight or user benefit explanation. Why is this update significant? ~100 characters.
3. "score": An integer (1-5) representing the importance of this news:
   - 5: Groundbreaking (e.g., Major model release like GPT-5, paradigm shift).
   - 4: Major Update (e.g., New significant feature, big performance boost).
   - 3: Standard Update (e.g., Improved UI, minor new tools).
   - 2: Minor/Maintenance (e.g., Small bug fixes, documentation).
   - 1: Very subtle changes.

If NO functional news is found, return exactly: {{"has_news": false}}

Example output:
{{
  "summary": "Google AI Studioにおいて、Gemini 1.5 Proのコンテキストウィンドウが大幅に拡張されました。",
  "why": "より長いコードや膨大なドキュメントを一度に処理できるようになり、開発効率が劇的に向上します。",
  "score": 5
}}

Return ONLY the JSON. No markdown fencing.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt
        )
        text = response.text.strip()
        
        # Remove markdown fencing if present
        clean_json = re.sub(r'```json\s*|\s*```', '', text)
        data = json.loads(clean_json)
        
        if data.get("has_news") is False:
            return None
            
        return {
            "summary": data.get("summary", ""),
            "why": data.get("why", "詳細をご確認ください。"),
            "score": int(data.get("score", 3))
        }
    except Exception as e:
        print(f"    ⚠️ Gemini Error: {e}")
        return {"error": str(e)}
