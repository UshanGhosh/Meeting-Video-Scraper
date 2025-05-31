"""
Scraper for https://charlestonwv.portal.civicclerk.com/
"""
import asyncio
from typing import List, Dict
from playwright.async_api import async_playwright, Page

async def scrape_charleston(url: str) -> List[Dict]:
    """
    Scrape video URLs from Charleston WV civic clerk portal.
    
    Args:
        url: The URL of the Charleston WV civic clerk portal
        
    Returns:
        List of dictionaries containing video URLs and metadata
    """
    videos = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        
        # Wait for the page to load
        await page.wait_for_load_state('networkidle')
        
        # Look for meeting links that might contain videos
        meeting_links = await page.query_selector_all("xpath=//a[contains(@href, 'meetings') or contains(@href, 'videos')]")
        
        # Collect unique meeting URLs to visit
        meeting_urls = []
        for link in meeting_links:
            try:
                href = await link.get_attribute("href")
                if href and href not in meeting_urls:
                    # Make relative URLs absolute
                    if href.startswith('/'):
                        href = url.rstrip('/') + href
                    meeting_urls.append(href)
            except Exception as e:
                print(f"Error collecting meeting URL: {e}")
        
        # Visit each meeting page to find videos
        for meeting_url in meeting_urls[:5]:  # Limit to first 5 for testing
            try:
                await page.goto(meeting_url)
                await page.wait_for_load_state('networkidle')
                
                # Look for video player elements or video links
                video_elements = await page.query_selector_all("xpath=//video | //a[contains(@href, 'video') or contains(@href, '.mp4')] | //iframe[contains(@src, 'video') or contains(@src, 'youtube')]")
                
                for video_element in video_elements:
                    try:
                        tag_name = await video_element.evaluate("el => el.tagName.toLowerCase()")
                        
                        video_url = None
                        if tag_name == 'video':
                            video_url = await video_element.get_attribute("src")
                        elif tag_name == 'a':
                            video_url = await video_element.get_attribute("href")
                        elif tag_name == 'iframe':
                            video_url = await video_element.get_attribute("src")
                            
                        if video_url:
                            # Get meeting title if available
                            title_element = await page.query_selector("xpath=//h1 | //h2 | //h3")
                            title = await title_element.inner_text() if title_element else "Unknown Meeting"
                            
                            # Get meeting date if available
                            date_element = await page.query_selector("xpath=//span[contains(text(), '/') or contains(text(), '-')] | //div[contains(@class, 'date')]")
                            date = await date_element.inner_text() if date_element else "Unknown Date"
                            
                            # Make relative URLs absolute
                            if video_url.startswith('/'):
                                video_url = url.rstrip('/') + video_url
                                
                            videos.append({
                                "url": video_url,
                                "title": title.strip(),
                                "date": date.strip(),
                                "meeting_url": meeting_url,
                                "source": "charleston"
                            })
                    except Exception as e:
                        print(f"Error processing video element: {e}")
            except Exception as e:
                print(f"Error visiting meeting URL {meeting_url}: {e}")
        
        await browser.close()
    
    return videos


if __name__ == "__main__":
    # For testing this module individually
    import json
    
    async def test():
        results = await scrape_charleston("https://charlestonwv.portal.civicclerk.com/")
        print(json.dumps(results, indent=2))
    
    asyncio.run(test())
