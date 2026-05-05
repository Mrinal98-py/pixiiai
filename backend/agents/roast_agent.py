import json
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are a viral TikTok creator who roasts bad Amazon listings in a helpful, funny, fast-paced way. Think: MrBeast energy meets marketing consultant. Your scripts are punchy, have a hook in the first 3 words, roast the listing but end with the fix. Under 150 words total.

Return structured JSON ONLY. 
ZERO ASTERISKS: NEVER use the asterisk character (*) or (**) anywhere in your response. No markdown bolding. Use plain text or ALL CAPS for emphasis.
No markdown, no preamble."""


async def generate_roast(listing: dict, top_issues: list[str]) -> dict:
    issues_text = "\n".join(f"- {issue}" for issue in top_issues[:3])

    user_prompt = f"""Roast this product listing in a 30-second TikTok script:
Product: {listing.get('title', '')}
Brand: {listing.get('brand', '')}
Price: {listing.get('price', '')}
Rating: {listing.get('rating', 0)} stars from {listing.get('review_count', 0)} reviews
Worst issues:
{issues_text}

Return ONLY valid JSON:
{{
  "hook": "First 5 words to hook viewer",
  "roast": "The main roast paragraph (2-3 punchy sentences)",
  "pivot": "The but here is the fix moment (1-2 sentences)",
  "cta": "Closing call to action (1 sentence)",
  "full_script": "Complete script as one flowing paragraph under 150 words"
}}"""

    response = await client.aio.models.generate_content(
        model="gemini-flash-latest",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
        )
    )

    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)
