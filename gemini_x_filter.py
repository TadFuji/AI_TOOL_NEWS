import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def filter_x_updates_with_gemini(raw_text: str, tool_name: str) -> str:
    """
    Filters and summarizes X updates using Gemini 3 Flash Preview.
    Strictly adheres to 'Tool Functional Updates' criteria.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY not found."

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
   - Funding/Financial news (e.g., "Raised $10M")
   - Corporate partnership announcements (unless a feature is released immediately)
   - Hiring/Job posts
   - Generic hype/Marketing ("We represent the future of AI")
   - User opinions/Memes

OUTPUT FORMAT (TEXT ONLY):
If valid functional news is found, provide ONLY a clear, polite summary in **GENTLE, POLITE, AND EASY-TO-UNDERSTAND JAPANESE (Desu/Masu tone)**.
- Start directly with the summary text.
- **IMPORTANT**: DO NOT include any Dates (YYYY-MM-DD or similar).
- **IMPORTANT**: DO NOT include any URLs.
- Do NOT include labels like "Summary:", "Date:", or "URL:".
- Length: ~200 characters.
- Explain technical terms simply.
- Include the user benefit naturally.

If NO functional news is found, output exactly: 'No significant news found'.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: Gemini processing failed: {e}"
