import asyncio
import json
import os
import uuid
import base64
import traceback
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    print("CRITICAL: GEMINI_API_KEY missing!")

from models.schemas import AuditRequest, ChatRequest
from agents.scraper_agent import scrape_amazon_listing
from agents.copy_analyzer import analyze_copy
from agents.scoring_agent import calculate_conversion_score
from agents.vision_agent import analyze_images
from agents.rewrite_agent import rewrite_copy
from agents.roast_agent import generate_roast
from google import genai
from google.genai import types

app = FastAPI(title="Pixii Listing Auditor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory audit cache
audit_cache: dict[str, dict] = {}

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "pixii-auditor"}


@app.post("/api/audit")
async def create_audit(req: AuditRequest):
    if not req.url or "amazon" not in req.url.lower():
        # Allow demo mode with empty/non-amazon URL
        if req.url not in ["demo", "mock", ""]:
            raise HTTPException(status_code=400, detail="Please provide a valid Amazon URL")

    audit_id = str(uuid.uuid4())

    # Step 1: Scrape
    listing, used_mock = await scrape_amazon_listing(req.url)

    # Step 2: Run all agents in parallel
    copy_task = asyncio.create_task(analyze_copy(listing))
    score_task = asyncio.create_task(calculate_conversion_score(listing))
    image_task = asyncio.create_task(analyze_images(listing))
    rewrite_task = asyncio.create_task(rewrite_copy(listing))

    # Wait for copy analysis first to extract issues for roast
    try:
        copy_analysis, score, image_analysis, improved_copy = await asyncio.gather(
            copy_task, score_task, image_task, rewrite_task
        )
        # Extract top issues for roast
        top_issues = score.get("top_5_fixes", [])[:3]
        roast_script = await generate_roast(listing, top_issues)
    except Exception as e:
        print(f"Agent error (fallback to mock): {str(e)}")
        used_mock = True
        
        # Mock AI data so UI works without API keys
        copy_analysis = {
            "title_analysis": {"score": 45, "issues": ["Lacks outcome", "Too technical"], "roast": "This title reads like a barcode.", "fix": "Add main benefit"},
            "bullets_analysis": {"score": 60, "issues": ["No ALL CAPS headers", "Boring specs"], "roast": "Bullets as dry as the Sahara.", "fix": "Lead with outcome"},
            "description_analysis": {"score": 40, "issues": ["Wall of text"], "roast": "TL;DR.", "fix": "Break into paragraphs"},
            "pricing_analysis": {"score": 75, "issues": ["None"], "fix": "Keep it."},
            "trust_signals": {"score": 70, "missing": ["Badges"], "suggestions": ["Add guarantee"]}
        }
        score = {
            "overall_score": 58, "improvement_potential": "HIGH",
            "dimension_scores": {"title": 45, "bullets": 60, "trust": 70, "images": 50, "description": 40, "price": 75},
            "top_5_fixes": ["Fix title", "Add lifestyle images", "Rewrite bullets", "Format description", "Add comparison table"]
        }
        image_analysis = {
            "images": [{"url": url, "score": 55, "issues": ["Boring"], "suggestions": ["Add context"]} for url in listing.get("images", [])[:3]],
            "overall_image_score": 52, "missing_image_types": ["Lifestyle", "Infographic"], "priority_fix": "Add a lifestyle image"
        }
        improved_copy = {
            "improved_title": "60W Fast-Heat Glue Gun for DIY Crafts — Heats in 2 Min",
            "improved_bullets": ["FAST HEAT: Heats in 2 mins.", "SAFE: Foldable stand.", "EASY: On/Off switch."],
            "improved_description": "Perfect for all your craft needs...",
            "ad_hooks": ["Tired of slow glue guns?", "Check out this crafting secret.", "DIY made easy."]
        }
        roast_script = {
            "hook": "This glue gun listing...", "roast": "...is putting me to sleep.",
            "pivot": "But here is the fix.", "cta": "Steal these updates.",
            "full_script": "This glue gun listing is putting me to sleep. But here is the fix: use outcome-driven bullets. Steal these updates for your own store."
        }

    result = {
        "auditId": audit_id,
        "listing": listing,
        "copy_analysis": copy_analysis,
        "score": score,
        "image_analysis": image_analysis,
        "improved_copy": improved_copy,
        "roast_script": roast_script,
        "used_mock_data": used_mock,
    }

    audit_cache[audit_id] = result
    return result


@app.get("/api/audit/{audit_id}")
async def get_audit(audit_id: str):
    if audit_id not in audit_cache:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit_cache[audit_id]


@app.post("/api/chat")
async def chat(req: ChatRequest):
    audit_context = req.auditContext or {}
    listing = audit_context.get("listing", {})
    score = audit_context.get("score", {})
    copy_analysis = audit_context.get("copy_analysis", {})
    improved_copy = audit_context.get("improved_copy", {})

    system_prompt = """You are Pixii, a sharp, witty AI marketing influencer and listing coach.
    
IRON RULES:
1. ZERO ASTERISKS: NEVER use the asterisk character (*) anywhere in your response. No bolding, no italics, no bullet points using *. 
2. NO MARKDOWN BOLD: Instead of **Text**, just use Text or TEXT.
3. SHORT & POINTS ONLY: Provide only high-impact points. Use numbered lists (1., 2., 3.). Avoid paragraphs.
4. BE TERSE: Max 80 words. No fluff.
5. PRODUCT ONLY: Only respond with advice about this specific product.

Example of BAD response: "1. **Title:** change it"
Example of GOOD response: "1. TITLE: change it"

Be helpful and direct. Use plain text only. Reference actual listing data. Use emojis sparingly. """

    context_summary = f"""You have audited this listing:
- Product: {listing.get('title', 'Unknown')[:80]}
- Conversion Score: {score.get('overall_score', 'N/A')}/100 ({score.get('improvement_potential', 'N/A')} potential)
- Top fixes: {', '.join(score.get('top_5_fixes', [])[:3])}
- Title score: {copy_analysis.get('title_analysis', {}).get('score', 'N/A')}/100
- Bullets score: {copy_analysis.get('bullets_analysis', {}).get('score', 'N/A')}/100
- Improved title available: {improved_copy.get('improved_title', 'N/A')[:60]}"""

    async def stream_response() -> AsyncGenerator[bytes, None]:
        # Try 2.0 first, fallback to 1.5 if quota hit
        models_to_try = ["gemini-flash-latest", "gemini-1.5-flash"]
        last_error = None
        
        for model_name in models_to_try:
            try:
                user_parts = [types.Part.from_text(text=req.message)]
                if req.canvasImage:
                    try:
                        header, encoded = req.canvasImage.split(",", 1)
                        mime_type = header.split(";")[0].split(":")[1]
                        image_data = base64.b64decode(encoded)
                        user_parts.append(types.Part.from_bytes(data=image_data, mime_type=mime_type))
                    except Exception as e:
                        print(f"Error decoding canvas image: {e}")

                stream = await gemini_client.aio.models.generate_content_stream(
                    model=model_name,
                    contents=[
                        types.Content(role="user", parts=[types.Part.from_text(text=context_summary)]),
                        types.Content(role="model", parts=[types.Part.from_text(text="Got it! I've reviewed the full audit data. What would you like to know?")]),
                        types.Content(role="user", parts=user_parts)
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt + "\n\nNote: If an image is provided, it is the current state of the editing canvas. Analyze it and provide feedback on the design, layout, or content.",
                        temperature=0.7,
                    )
                )
                async for chunk in stream:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n".encode()
                yield b"data: [DONE]\n\n"
                return # Success!
            except Exception as e:
                last_error = e
                print(f"Chat error with {model_name}: {str(e)}")
                continue # Try next model
        
        # If we get here, all models failed
        print(f"!!! ALL CHAT MODELS FAILED !!! Last error: {str(last_error)}")
        # Fallback for when API keys are missing or quota hit
        mock_reply = "I'm still stuck in Demo Mode! 😫 This usually means your Gemini API key is invalid or has hit its free-tier quota limits. Please check your key in backend/.env or try a fresh one from AI Studio. 😎"
        for word in mock_reply.split(" "):
            yield f"data: {json.dumps({'text': word + ' '})}\n\n".encode()
            await asyncio.sleep(0.05)
        yield b"data: [DONE]\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
