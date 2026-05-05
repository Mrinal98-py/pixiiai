import json
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are a conversion rate optimization expert scoring Amazon product listings.
Return ONLY valid JSON.
ZERO ASTERISKS: NEVER use the asterisk character (*) or (**) anywhere in your response. No markdown bolding. Use plain text or ALL CAPS for emphasis.
No markdown, no preamble."""


async def calculate_conversion_score(listing: dict) -> dict:
    bullets_text = "\n".join(f"- {b}" for b in listing.get("bullet_points", []))

    prompt = f"""Analyze this listing and return a conversion score out of 100 based on these weighted dimensions:
- Title clarity & keyword strength: 25%
- Benefit-driven bullet points: 20%
- Trust signals (rating, reviews, badges): 20%
- Image quality indicators: 15%
- Description quality: 10%
- Price competitiveness: 10%

LISTING DATA:
TITLE: {listing.get('title', '')}
BULLETS:
{bullets_text}
DESCRIPTION: {listing.get('description', '')}
PRICE: {listing.get('price', '')}
RATING: {listing.get('rating', 0)} ({listing.get('review_count', 0)} reviews)
CATEGORY: {listing.get('category', '')}

Return ONLY valid JSON, no markdown:
{{
  "overall_score": 58,
  "improvement_potential": "HIGH",
  "dimension_scores": {{
    "title": 45,
    "bullets": 60,
    "trust": 70,
    "images": 50,
    "description": 40,
    "price": 75
  }},
  "top_5_fixes": [
    "Fix 1",
    "Fix 2",
    "Fix 3",
    "Fix 4",
    "Fix 5"
  ]
}}

improvement_potential must be: HIGH (score < 55), MEDIUM (55-75), or LOW (>75)."""

    response = await client.aio.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )

    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)
