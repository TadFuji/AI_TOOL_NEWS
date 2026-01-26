import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    print("Error: XAI_API_KEY not found.")
    exit()

url = "https://api.x.ai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}"
}

print("Fetching xAI models...")
try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        models = response.json().get('data', [])
        for m in models:
            print(f"- {m['id']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Exception: {e}")
