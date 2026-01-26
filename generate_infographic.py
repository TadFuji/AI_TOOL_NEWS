import os
import google.genai
from google.genai import types
from dotenv import load_dotenv
import base64

load_dotenv()

def generate_infographic():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found.")
        return

    client = google.genai.Client(api_key=api_key)
    
    # Model: Nano Banana Pro (gemini-3-pro-image-preview)
    # Trying with prefix
    model_id = "models/gemini-3-pro-image-preview"

    prompt = """
    Create a high-quality professional infographic comparing two AI automation workflows in a dark mode tech style.

    LEFT SIDE: Title "AI News Top 10 (Daily Bot)"
    - Icon: RSS Feed
    - AI Brain: "Gemini 3 Flash"
    - Output 1: LINE App (List)
    - Output 2: Web Browser
    - Output 3: X Logo (Thread Icon)
    - Schedule: "07:00 AM Daily"

    RIGHT SIDE: Title "AI Tool News (Hourly Bot)"
    - Icon: X / Twitter Logo (Patrol)
    - AI Brain: "Grok 4.1 Fast"
    - Output 1: X Logo (Breaking News)
    - Output 2: Web Browser
    - Schedule: "Hourly"

    Visual Style: Modern, Neon, flowchart, dark background, schematic, highly detailed, 8k resolution.
    """

    print(f"🎨 Generating infographic using {model_id}...")
    
    print(f"🎨 Generating infographic using {model_id} via generate_content...")
    
    print(f"🎨 Generating infographic using {model_id} via generate_content (Standard)...")
    
    try:
        # Retry with NO explicit config, just the prompt
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        
        # Check response parts for images
        if response.candidates and response.candidates[0].content.parts:
            for i, part in enumerate(response.candidates[0].content.parts):
                if part.inline_data:
                    # We found an image!
                    # The library might wrap bytes or strict checks
                    print(f"✅ Found Image Part in candidate {i}")
                    
                    try:
                        import base64
                        # Note: inline_data.data is usually bytes in the new SDK
                        img_data = part.inline_data.data
                        if isinstance(img_data, str):
                             img_data = base64.b64decode(img_data)
                             
                        output_file = f"workflow_infographic_{i+1}.png"
                        with open(output_file, "wb") as f:
                            f.write(img_data)
                        print(f"✅ Saved image to {output_file}")
                        return # Success
                    except Exception as e_img:
                        print(f"Error saving image: {e_img}")

                else:
                    print(f"Part {i} type: {type(part)}")
                    if hasattr(part, 'text') and part.text:
                         print(f"Text content: {part.text}")
        
        print("❌ No inline_data found in response.")
        # print(f"Raw Response: {response}")

    except Exception as e:
        print(f"❌ Generation failed: {e}") 


if __name__ == "__main__":
    generate_infographic()
