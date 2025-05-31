#!/usr/bin/env python3
"""
Script to examine the structure of the Regional Web TV site.
This will help identify the correct selectors for video elements.
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def examine_site_structure():
    """Examine the structure of the Regional Web TV site and save HTML for analysis."""
    url = "https://www.regionalwebtv.com/fredcc"
    print(f"Examining site structure: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Use headless=False to see the browser
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"Navigating to {url}...")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Take a screenshot for visual inspection
            print("Taking screenshot...")
            os.makedirs("output", exist_ok=True)
            await page.screenshot(path="output/regionalweb_screenshot.png", full_page=True)
            
            # Save page HTML for analysis
            print("Saving HTML...")
            html = await page.content()
            with open("output/regionalweb_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            # Look for different video element selectors
            for selector in [
                'a.w-video-card',  # Original selector
                '.video-card',
                '.video-item',
                '.video-container',
                'a[href*="video"]',
                '.featured-video',
                'div[class*="video"]',
                'div[id*="video"]'
            ]:
                elements = await page.query_selector_all(selector)
                print(f"Selector '{selector}': Found {len(elements)} elements")
                
                # If elements found, print more details about the first few
                if len(elements) > 0:
                    print(f"  Details for first {min(3, len(elements))} elements with '{selector}':")
                    for i, elem in enumerate(elements[:3]):
                        tag_name = await elem.evaluate("el => el.tagName.toLowerCase()")
                        html_snippet = await elem.evaluate("el => el.outerHTML.substring(0, 200) + '...'")
                        print(f"  {i+1}. Tag: {tag_name}")
                        print(f"     HTML: {html_snippet}")
                        
                        # Try to get href if it's an anchor
                        if tag_name == "a":
                            href = await elem.get_attribute("href")
                            print(f"     href: {href}")
                        
                        # Try to get any text content
                        text = await elem.text_content()
                        if text:
                            print(f"     Text: {text.strip()[:100]}...")
            
            # Wait to see the page if running in non-headless mode
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"Error examining site: {e}")
        finally:
            await browser.close()
            print("Browser closed")

if __name__ == "__main__":
    asyncio.run(examine_site_structure())
