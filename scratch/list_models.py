import os
from dotenv import load_dotenv
from google import genai
load_dotenv(dotenv_path=r"d:\Project\pixii\backend\.env")

key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=key)

try:
    print("Available models:")
    for model in client.models.list():
        print(f"- {model.name}")
except Exception as e:
    print(f"ERROR: {str(e)}")
