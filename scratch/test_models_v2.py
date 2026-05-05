import os
from dotenv import load_dotenv
from google import genai
load_dotenv(dotenv_path=r"d:\Project\pixii\backend\.env")

key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=key)

for model in ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"]:
    print(f"TESTING {model}...")
    try:
        response = client.models.generate_content(
            model=model,
            contents="Hi"
        )
        print(f"SUCCESS {model}: {response.text}")
        break
    except Exception as e:
        print(f"ERROR {model}: {str(e)}")
