import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GOOGLE_API_KEY")

url_models = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
try:
    resp = requests.get(url_models)
    print("Models Status Code:", resp.status_code)
    if resp.status_code == 200:
        models = resp.json().get("models", [])
        for m in models:
            if "embed" in m.get("name", "").lower():
                print("Found embedding model:", m["name"])
    else:
        print(resp.text)
except Exception as e:
    print("Request failed:", e)
