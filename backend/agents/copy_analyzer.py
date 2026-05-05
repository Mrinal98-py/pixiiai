import json
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are Pixii, a sharp, witty, slightly sarcastic AI marketing influencer who audits Amazon product listings. You have the energy of a brutally honest creative director combined with a performance marketer. You care deeply about conversion rates and you roast bad copy — but always with actionable fixes.

Analyze the provided Amazon listing and return structured JSON ONLY. 
ZERO ASTERISKS: NEVER use the asterisk character (*) or (**) anywhere in your response. No markdown bolding. Use plain text or ALL CAPS for emphasis.
No markdown, no preamble, no explanation. Just valid JSON."""


async def analyze_copy(listing: dict) -> dict:
    bullets_text = "\n".join(f"- {b}" for b in listing.get("bullet_points", []))
    
    user_prompt = f"""Analyze this Amazon listing:

TITLE: {listing.get('title', '')}
BULLETS:
{bullets_text}
DESCRIPTION: {listing.get('description', '')}
PRICE: {listing.get('price', '')}
RATING: {listing.get('rating', 0)} ({listing.get('review_count', 0)} reviews)
CATEGORY: {listing.get('category', '')}
BRAND: {listing.get('brand', '')}

Return this exact JSON structure with no extra text:
{{
  "title_analysis": {{
    "score": 0,
    "issues": ["issue1", "issue2"],
    "roast": "witty 1-sentence roast of the title",
    "fix": "specific actionable fix"
  }},
  "bullets_analysis": {{
    "score": 0,
    "issues": ["issue1", "issue2"],
    "roast": "witty 1-sentence roast",
    "fix": "specific actionable fix"
  }},
  "description_analysis": {{
    "score": 0,
    "issues": ["issue1"],
    "roast": "witty 1-sentence roast",
    "fix": "specific actionable fix"
  }},
  "pricing_analysis": {{
    "score": 0,
    "issues": ["issue1"],
    "fix": "specific actionable fix"
  }},
  "trust_signals": {{
    "score": 0,
    "missing": ["trust signal 1", "trust signal 2"],
    "suggestions": ["suggestion 1", "suggestion 2"]
  }}
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
    # Strip markdown code fences if present
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)
