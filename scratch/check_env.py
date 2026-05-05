import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("GEMINI_API_KEY")
print(f"KEY_FOUND: {key is not None}")
if key:
    print(f"KEY_START: {key[:5]}...")
    print(f"KEY_LENGTH: {len(key)}")
