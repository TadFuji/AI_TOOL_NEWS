import os
import json
import requests
import datetime
import re

# Load API Key directly for testing
def load_api_key():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("XAI_API_KEY="):
                    return line.strip().split("=")[1]
    return os.environ.get("XAI_API_KEY")

API_KEY = load_api_key()

# Testing grok-4 family as required by server-side tools
MODELS_TO_TEST = ["grok-4-1-fast-non-reasoning"]

def test_model(model_name):
    print(f"\n--- Testing Model: {model_name} (Endpoint: /v1/responses) ---")
    url = "https://api.x.ai/v1/responses"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # Prompt asking for specific RECENT real-time data
    prompt = "Fetch the very latest tweet from @OpenAI. Output the Date and Content exactly."
    
    # Tool definition for x_search (Server-side tool)
    # Reverting to function definition as live_search is deprecated
    # Using specific definition mentioned in documentation examples
    tools = [
        {
            "type": "x_search"
        }
    ]

    payload = {
        "input": prompt,
        "model": model_name,
        "stream": False, 
        "temperature": 0,
        "tools": tools,
        "tool_choice": "auto" 
    }
    
    try:
        start = datetime.datetime.now()
        response = requests.post(url, headers=headers, data=json.dumps(payload), stream=False)
        
        if response.status_code == 200:
            print("Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Exception: {e}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("Error: API Key not found.")
    else:
        for m in MODELS_TO_TEST:
            test_model(m)
