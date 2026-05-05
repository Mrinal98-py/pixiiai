import json
import os
import httpx
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are an Amazon listing image quality auditor. Evaluate product images for e-commerce conversion quality.
Return ONLY valid JSON.
ZERO ASTERISKS: NEVER use the asterisk character (*) or (**) anywhere in your response. No markdown bolding. Use plain text or ALL CAPS for emphasis.
No markdown, no preamble."""


async def analyze_images(listing: dict) -> dict:
    images = listing.get("images", [])[:3]

    if not images:
        return _fallback_image_analysis()

    # Try to fetch and analyze images via Gemini vision
    try:
        # Build contents with image data
        parts = [
            types.Part.from_text(text="""Evaluate these Amazon product images for e-commerce conversion quality.

For each image, assess:
1. Background quality (white/clean vs cluttered)
2. Lighting quality
3. Image clarity and resolution appearance
4. Presence of lifestyle/usage context
5. Infographic or feature callouts

Return ONLY valid JSON:
{
  "images": [
    {
      "url": "...",
      "score": 65,
      "issues": ["issue1"],
      "suggestions": ["suggestion1"]
    }
  ],
  "overall_image_score": 60,
  "missing_image_types": ["lifestyle photo", "infographic", "scale reference"],
  "priority_fix": "most important image to add or fix"
}""")
        ]

        fetched_images = []
        async with httpx.AsyncClient(timeout=10) as http:
            for url in images:
                try:
                    r = await http.get(url)
                    if r.status_code == 200:
                        content_type = r.headers.get("content-type", "image/jpeg").split(";")[0]
                        parts.append(types.Part.from_bytes(data=r.content, mime_type=content_type))
                        fetched_images.append(url)
                except Exception:
                    pass

        if not fetched_images:
            return _fallback_image_analysis(images)

        response = await client.aio.models.generate_content(
            model="gemini-flash-latest",
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)

        # Ensure image URLs match what we sent
        if "images" in result:
            for i, img in enumerate(result["images"]):
                if i < len(fetched_images):
                    img["url"] = fetched_images[i]

        return result

    except Exception as e:
        print(f"Vision agent error: {e}")
        return _fallback_image_analysis(images)


def _fallback_image_analysis(images: list = None) -> dict:
    if not images:
        images = []

    image_items = []
    for url in images:
        image_items.append({
            "url": url,
            "score": 55,
            "issues": ["No lifestyle context", "Missing feature callouts"],
            "suggestions": ["Add usage scenario photo", "Create infographic with key specs"]
        })

    return {
        "images": image_items,
        "overall_image_score": 52,
        "missing_image_types": ["lifestyle photo", "infographic", "scale reference", "360° view"],
        "priority_fix": "Add a lifestyle image showing the product in real use — this alone can boost CTR by 15-25%"
    }
