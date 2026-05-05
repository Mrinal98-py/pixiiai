import httpx
import json
import asyncio

async def test_chat():
    url = "http://localhost:8000/api/chat"
    payload = {
        "message": "Hello Pixii, can you see this?",
        "auditId": "test-id",
        "auditContext": {
            "listing": {"title": "Test Product"},
            "score": {"overall_score": 80},
            "copy_analysis": {},
            "improved_copy": {}
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload, timeout=20.0) as response:
                print(f"Status Code: {response.status_code}")
                async for line in response.aiter_lines():
                    if line:
                        print(line)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
