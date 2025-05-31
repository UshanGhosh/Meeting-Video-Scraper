import asyncio
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def scrape_dauphin_county(url: str) -> List[Dict[str, Any]]:
    """
    Scrape video information from Dauphin County Facebook page.
    
    Args:
        url: The URL of the Dauphin County Facebook videos page
        
    Returns:
        List of dictionaries containing video information
    """
    videos = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to the URL
        await page.goto(url, wait_until="networkidle")
        
        # Wait longer for the page to fully render before starting
        print("Waiting for page to fully render...")
        await asyncio.sleep(10)  # 10 second wait for better rendering
        
        # Scroll more extensively to load more videos
        print("Scrolling to load more videos...")
        for i in range(10):  # Increased from 5 to 10 scrolls
            print(f"Scroll iteration {i+1}/10")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)  # Increased wait time
            
            # Every other iteration, scroll back up and then down to trigger more content loading
            if i % 2 == 0:
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                
            # Occasionally click 'See More' buttons if they exist
            try:
                see_more_buttons = await page.query_selector_all("div[role='button']:has-text('See more')")
                for button in see_more_buttons[:5]:  # Limit to 5 buttons per iteration
                    await button.click()
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error clicking 'See More' buttons: {str(e)}")
        
        # Get the page content
        content = await page.content()
        await browser.close()
    
    # Parse content with BeautifulSoup
    soup = BeautifulSoup(content, "html.parser")
    
    # Find video links with multiple selectors to get more videos
    video_links = []
    
    # Original selector
    links1 = soup.select("a[aria-hidden='false'][class*='x1i10hfl']")
    print(f"Found {len(links1)} videos with primary selector")
    video_links.extend(links1)
    
    # Additional selectors for more video links
    links2 = soup.select("a[href*='/videos/']")
    print(f"Found {len(links2)} videos with secondary selector")
    video_links.extend(links2)
    
    # Third selector focusing on Facebook video formatting
    links3 = soup.select("a[href*='facebook.com'][href*='/videos/']")
    print(f"Found {len(links3)} videos with tertiary selector")
    video_links.extend(links3)
    
    # Deduplicate links by href
    unique_hrefs = set()
    deduplicated_links = []
    
    for link in video_links:
        href = link.get("href")
        if href and href not in unique_hrefs and "/videos/" in href:
            unique_hrefs.add(href)
            deduplicated_links.append(link)
    
    video_links = deduplicated_links
    print(f"Found {len(video_links)} unique video links after deduplication")
    
    for link in video_links:
        href = link.get("href")
        if not href or "/videos/" not in href:
            continue
        
        # Normalize the URL
        if not href.startswith("https://"):
            if href.startswith("/"):
                href = f"https://www.facebook.com{href}"
            else:
                href = f"https://www.facebook.com/{href}"
        
        # Find the caption/title using multiple selectors
        title = "No title"
        
        # Try multiple potential title selectors
        title_selectors = [
            "span[class*='xdj266r']",  # Original selector
            "span[dir='auto']",  # Common text container
            "div[dir='auto']",  # Another common text container
            "h3",  # Heading that might contain title
            "span[class*='xt0b8zv']",  # Another potential class
            "div[data-ad-preview='message']",  # Ad preview might contain title
            "div[class*='userContent']",  # User content
            "div[data-ad-comet-preview='message']",  # Ad preview
            ".x8182xy"  # Common Facebook content class
        ]
        
        # Try each selector in order until we find content
        for selector in title_selectors:
            caption_element = link.select_one(selector)
            if caption_element and caption_element.get_text(strip=True):
                title = caption_element.get_text(strip=True)
                break
                
        # If no title found from direct selectors, try parent elements
        if title == "No title":
            # Try to find title in parent elements
            parent = link.parent
            for _ in range(3):  # Check up to 3 levels up
                if parent:
                    text_content = parent.get_text(strip=True)
                    if text_content and len(text_content) > 10 and len(text_content) < 200:
                        title = text_content
                        break
                    parent = parent.parent
                    
        # Clean up the title if found
        if title != "No title":
            # Remove excessive whitespace
            title = re.sub(r'\s+', ' ', title).strip()
            # Truncate if too long
            if len(title) > 100:
                title = title[:97] + "..."
        
        # Extract date from caption
        date = None
        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', title)
        if date_match:
            date_str = date_match.group(1)
            try:
                # Try to parse the date
                date = datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
            except ValueError:
                try:
                    date = datetime.strptime(date_str, "%m-%d-%Y").strftime("%Y-%m-%d")
                except ValueError:
                    date = None
        
        videos.append({
            "url": href,
            "title": title,
            "date": date,
            "source_type": "video"
        })
    
    return videos

if __name__ == "__main__":
    import sys
    
    # Default URL for Dauphin County Facebook Videos
    url = "https://www.facebook.com/DauphinCountyPA/videos"
    
    # Allow URL override from command line
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    # Run the scraper
    print(f"Starting scraper for {url}")
    videos = asyncio.run(scrape_dauphin_county(url))
    
    # Save results to JSON file
    output_file = "../output/dauphin_county_videos.json"
    with open(output_file, "w") as f:
        json.dump({"base_url": url, "medias": videos}, f, indent=2)
    
    print(f"Scraped {len(videos)} videos from {url}")
    print(f"Results saved to {output_file}")
