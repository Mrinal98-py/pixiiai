import os
from dotenv import load_dotenv
from google import genai

env_path = r"d:\Project\pixii\backend\.env"
print(f"CHECKING PATH: {env_path}")
print(f"EXISTS: {os.path.exists(env_path)}")

load_dotenv(dotenv_path=env_path)

key = os.getenv("GEMINI_API_KEY")
print(f"KEY_FOUND: {key is not None}")
if key:
    print(f"KEY: {key[:5]}...")

client = genai.Client(api_key=key)

try:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Hi"
    )
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"ERROR: {str(e)}")
