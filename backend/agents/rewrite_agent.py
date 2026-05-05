import json
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are Pixii, a sharp, witty, slightly sarcastic AI marketing influencer who rewrites Amazon product listings to maximize conversion rate. You have the energy of a brutally honest creative director combined with a performance marketer.

Return structured JSON ONLY. 
ZERO ASTERISKS: NEVER use the asterisk character (*) or (**) anywhere in your response. No markdown bolding. Use plain text or ALL CAPS for emphasis.
No markdown, no preamble, no explanation. Just valid JSON."""


async def rewrite_copy(listing: dict) -> dict:
    bullets_text = "\n".join(f"- {b}" for b in listing.get("bullet_points", []))

    user_prompt = f"""Rewrite this Amazon listing to maximize conversion rate.

Original listing:
TITLE: {listing.get('title', '')}
BULLETS:
{bullets_text}
DESCRIPTION: {listing.get('description', '')}
CATEGORY: {listing.get('category', '')}
PRICE: {listing.get('price', '')}
BRAND: {listing.get('brand', '')}

Rules:
- Title: 150-200 chars, lead with primary keyword, include use case and outcome
- Bullets: Start each with ALL CAPS benefit label followed by colon. Lead with outcome, follow with feature.
- Description: Narrative style, paint the problem then solution. End with CTA.
- Keep all factual specs accurate. Do not invent features.
- Ad hooks: three hooks for different awareness stages

Return ONLY valid JSON:
{{
  "improved_title": "...",
  "improved_bullets": ["BENEFIT LABEL: outcome — feature.", "...", "...", "...", "..."],
  "improved_description": "...",
  "ad_hooks": [
    "hook 1 (problem-aware)",
    "hook 2 (curiosity-based)",
    "hook 3 (social proof)"
  ]
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
