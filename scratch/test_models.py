import os
from dotenv import load_dotenv
from google import genai

env_path = r"d:\Project\pixii\backend\.env"
load_dotenv(dotenv_path=env_path)

key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=key)

for model in ["gemini-1.5-flash", "gemini-1.5-pro"]:
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
