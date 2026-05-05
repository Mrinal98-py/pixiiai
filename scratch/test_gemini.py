import os
from dotenv import load_dotenv
from google import genai
load_dotenv()

key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=key)

try:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Hi"
    )
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"ERROR: {str(e)}")
