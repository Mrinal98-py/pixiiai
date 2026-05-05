import asyncio
import json
import re
from playwright.async_api import async_playwright
from utils.mock_data import MOCK_LISTING


async def scrape_amazon_listing(url: str) -> tuple[dict, bool]:
    """Returns (listing_data, used_mock). Falls back to mock if blocked."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # Check for bot detection
            content = await page.content()
            if "Robot Check" in content or "Enter the characters" in content:
                await browser.close()
                return MOCK_LISTING, True

            # Extract title
            title = ""
            try:
                title_el = await page.query_selector("#productTitle")
                if title_el:
                    title = (await title_el.text_content() or "").strip()
            except Exception:
                pass

            if not title:
                await browser.close()
                return MOCK_LISTING, True

            # Extract bullets
            bullets = []
            try:
                bullet_els = await page.query_selector_all(
                    "#feature-bullets li span.a-list-item"
                )
                for el in bullet_els[:8]:
                    text = (await el.text_content() or "").strip()
                    if text and len(text) > 5:
                        bullets.append(text)
            except Exception:
                pass

            # Extract price
            price = ""
            try:
                price_el = await page.query_selector(".a-price .a-offscreen")
                if price_el:
                    price = (await price_el.text_content() or "").strip()
            except Exception:
                pass

            # Extract rating
            rating = 0.0
            try:
                rating_el = await page.query_selector("#acrPopover span.a-size-base.a-color-base")
                if not rating_el:
                    rating_el = await page.query_selector("#acrPopover")
                if rating_el:
                    title_attr = await rating_el.get_attribute("title")
                    if title_attr:
                        match = re.search(r"(\d+\.?\d*)", title_attr)
                        if match:
                            rating = float(match.group(1))
            except Exception:
                pass

            # Extract review count
            review_count = 0
            try:
                review_el = await page.query_selector("#acrCustomerReviewText")
                if review_el:
                    text = (await review_el.text_content() or "").strip()
                    match = re.search(r"([\d,]+)", text)
                    if match:
                        review_count = int(match.group(1).replace(",", ""))
            except Exception:
                pass

            # Extract images
            images = []
            try:
                img_els = await page.query_selector_all("#altImages img")
                for el in img_els[:6]:
                    src = await el.get_attribute("src")
                    if src and "sprite" not in src:
                        # Convert thumbnail to full size
                        src = re.sub(r"\._[A-Z0-9_,]+_\.", ".", src)
                        images.append(src)
            except Exception:
                pass

            # Extract description
            description = ""
            try:
                desc_el = await page.query_selector("#productDescription p")
                if desc_el:
                    description = (await desc_el.text_content() or "").strip()
                if not description:
                    desc_el = await page.query_selector("#productDescription")
                    if desc_el:
                        description = (await desc_el.text_content() or "").strip()[:500]
            except Exception:
                pass

            # Extract ASIN from URL
            asin = ""
            match = re.search(r"/dp/([A-Z0-9]{10})", url)
            if match:
                asin = match.group(1)

            # Extract brand
            brand = ""
            try:
                brand_el = await page.query_selector("#bylineInfo")
                if brand_el:
                    brand = (await brand_el.text_content() or "").strip()
                    brand = re.sub(r"^(Brand|Visit the|Store):?\s*", "", brand).strip()
            except Exception:
                pass

            await browser.close()

            listing = {
                "title": title or MOCK_LISTING["title"],
                "bullet_points": bullets or MOCK_LISTING["bullet_points"],
                "description": description or MOCK_LISTING["description"],
                "images": images or MOCK_LISTING["images"],
                "price": price or MOCK_LISTING["price"],
                "rating": rating or MOCK_LISTING["rating"],
                "review_count": review_count or MOCK_LISTING["review_count"],
                "reviews_summary": MOCK_LISTING["reviews_summary"],
                "asin": asin or MOCK_LISTING["asin"],
                "category": MOCK_LISTING["category"],
                "brand": brand or MOCK_LISTING["brand"],
            }
            return listing, False

    except Exception as e:
        print(f"Scraper error: {e}")
        return MOCK_LISTING, True
