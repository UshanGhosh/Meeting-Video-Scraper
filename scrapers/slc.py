"""
Scraper for https://www.youtube.com/@SLCLiveMeetings/streams
"""
import asyncio
import re
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright, Page

async def scrape_slc(url: str) -> List[Dict]:
    """
    Scrape video URLs from Salt Lake City YouTube channel.
    
    This function will scrape multiple sections of the YouTube channel
    to collect as many videos as possible (80-100 videos).
    
    Args:
        url: The URL of the SLC YouTube channel streams page
        
    Returns:
        List of dictionaries containing video URLs and metadata
    """
    videos = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        
        # Use a stealth page to avoid YouTube bot detection
        page = await context.new_page()
        
        # First visit the main channel page to get all channel sections
        channel_url = "https://www.youtube.com/@SLCLiveMeetings"
        print(f"Visiting main channel page: {channel_url}")
        await page.goto(channel_url)
        await page.wait_for_load_state('networkidle')
        
        # Handle cookie consent if present
        try:
            consent_button = await page.query_selector('button:has-text("I agree"), button:has-text("Accept"), button:has-text("Accept all")')
            if consent_button:
                await consent_button.click()
                await page.wait_for_timeout(1000)
        except Exception as e:
            print(f"No cookie consent dialog found or error handling it: {e}")
        
        # First collect all sections to visit (Videos, Playlists, Live, etc.)
        sections_to_visit = []
        
        # Add the main sections
        sections_to_visit.append({"url": url, "name": "Streams"})
        sections_to_visit.append({"url": f"{channel_url}/videos", "name": "Videos"})
        
        print(f"Will scrape {len(sections_to_visit)} channel sections")
        
        # Visit each section to collect videos
        for section in sections_to_visit:
            section_url = section["url"]
            section_name = section["name"]
            
            print(f"Scraping section: {section_name} at {section_url}")
            await page.goto(section_url)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)  # Wait for JS to load
            
            # Very aggressive scrolling - up to 30 times with longer pauses
            last_height = 0
            for scroll_count in range(30):
                # Scroll down to bottom
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Wait to load more content - longer wait time
                await page.wait_for_timeout(3000)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = await page.evaluate("document.body.scrollHeight")
                if scroll_count % 3 == 0:
                    print(f"Scrolled {scroll_count} times in {section_name}, height: {new_height}px")
                
                if new_height == last_height:
                    # If heights are the same, we've probably reached the end
                    print(f"No new content after {scroll_count} scrolls in section {section_name}")
                    break
                    
                last_height = new_height
            
            # After scrolling, collect all possible video links using multiple selectors
            print(f"Collecting videos from section {section_name}...")
            
            # 1. Standard video containers
            video_containers = await page.query_selector_all('ytd-grid-video-renderer, ytd-video-renderer')
            print(f"Found {len(video_containers)} video containers in {section_name}")
            
            # Process video containers
            for container in video_containers:
                try:
                    # Get video link
                    link_element = await container.query_selector('a#thumbnail[href*="/watch"]')
                    if not link_element:
                        continue
                        
                    video_url = await link_element.get_attribute("href")
                    if not video_url or "/watch" not in video_url:
                        continue
                    
                    # Ensure URL is absolute
                    if video_url.startswith('/'):
                        video_url = f"https://www.youtube.com{video_url}"
                    elif not video_url.startswith("http"):
                        video_url = f"https://www.youtube.com/{video_url}"
                    
                    # Get video title
                    title = "SLC Meeting Video"
                    title_element = await container.query_selector('#video-title, yt-formatted-string#video-title')
                    if title_element:
                        title_text = await title_element.inner_text()
                        if title_text and len(title_text.strip()) > 0:
                            title = title_text.strip()
                    
                    # Extract date from title
                    formatted_date = extract_date_from_title(title)
                    
                    # Add to videos list if not duplicate
                    is_duplicate = any(video["url"] == video_url for video in videos)
                    if not is_duplicate:
                        videos.append({
                            "url": video_url,
                            "title": title,
                            "date": formatted_date,
                            "source": "slc_youtube"
                        })
                        
                except Exception as e:
                    print(f"Error processing video container: {e}")
            
            # 2. Direct video links - find all links to watch videos
            video_links = await page.query_selector_all('a[href*="/watch?v="]')
            print(f"Found {len(video_links)} direct video links in {section_name}")
            
            # Process direct links
            for link in video_links:
                try:
                    video_url = await link.get_attribute("href")
                    if not video_url or "/watch?v=" not in video_url:
                        continue
                    
                    # Ensure URL is absolute
                    if video_url.startswith('/'):
                        video_url = f"https://www.youtube.com{video_url}"
                    elif not video_url.startswith("http"):
                        video_url = f"https://www.youtube.com/{video_url}"
                    
                    # Check for duplicates
                    is_duplicate = any(video["url"] == video_url for video in videos)
                    if is_duplicate:
                        continue
                    
                    # Try to get title
                    title = "SLC Meeting Video"
                    title_element = None
                    
                    # Try multiple approaches to find title
                    # 1. Check if link itself has a title attribute
                    title_attr = await link.get_attribute("title")
                    if title_attr and len(title_attr) > 5:
                        title = title_attr
                    else:
                        # 2. Look for nearby title elements
                        title_element = await link.query_selector('xpath=.//*[contains(@id, "title")] | ./following::*[contains(@id, "title")][1]')
                        if title_element:
                            title_text = await title_element.inner_text()
                            if title_text and len(title_text.strip()) > 5:
                                title = title_text.strip()
                    
                    # Extract date from title
                    formatted_date = extract_date_from_title(title)
                    
                    videos.append({
                        "url": video_url,
                        "title": title,
                        "date": formatted_date,
                        "source": "slc_youtube"
                    })
                    
                except Exception as e:
                    print(f"Error processing video link: {e}")
            
            print(f"Collected {len(videos)} videos so far...")
            
            # If we have enough videos, we can stop scraping more sections
            if len(videos) >= 100:
                print(f"Reached target of {len(videos)} videos, stopping section scraping")
                break
        
        # Visit playlists section as a fallback if we don't have enough videos
        if len(videos) < 80:
            print("Not enough videos found, trying to scrape playlists section...")
            playlists_url = f"{channel_url}/playlists"
            
            await page.goto(playlists_url)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)  # Wait for JS to load
            
            # Find playlist links
            playlist_items = await page.query_selector_all('ytd-grid-playlist-renderer a#thumbnail, ytd-playlist-renderer a#thumbnail')
            print(f"Found {len(playlist_items)} playlists")
            
            # Visit up to 3 playlists to collect more videos
            for i, playlist_item in enumerate(playlist_items[:3]):
                try:
                    playlist_url = await playlist_item.get_attribute('href')
                    if not playlist_url:
                        continue
                        
                    # Make sure URL is absolute
                    if playlist_url.startswith('/'):
                        playlist_url = f"https://www.youtube.com{playlist_url}"
                    
                    print(f"Visiting playlist {i+1}: {playlist_url}")
                    await page.goto(playlist_url)
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(3000)
                    
                    # Scroll in the playlist page
                    for _ in range(10):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(2000)
                    
                    # Collect videos from the playlist
                    playlist_videos = await page.query_selector_all('ytd-playlist-video-renderer a#video-title')
                    print(f"Found {len(playlist_videos)} videos in playlist {i+1}")
                    
                    for video_element in playlist_videos:
                        try:
                            video_url = await video_element.get_attribute('href')
                            if not video_url or "/watch" not in video_url:
                                continue
                                
                            # Ensure URL is absolute
                            if video_url.startswith('/'):
                                video_url = f"https://www.youtube.com{video_url}"
                            
                            # Check for duplicates
                            is_duplicate = any(video["url"] == video_url for video in videos)
                            if is_duplicate:
                                continue
                            
                            # Get title
                            title = await video_element.inner_text()
                            if not title or len(title.strip()) < 1:
                                title = "SLC Meeting Video"
                            
                            # Extract date from title
                            formatted_date = extract_date_from_title(title)
                            
                            videos.append({
                                "url": video_url,
                                "title": title,
                                "date": formatted_date,
                                "source": "slc_youtube"
                            })
                            
                        except Exception as e:
                            print(f"Error processing playlist video: {e}")
                    
                    # If we have enough videos, stop visiting more playlists
                    if len(videos) >= 100:
                        print(f"Reached target of {len(videos)} videos from playlists")
                        break
                        
                except Exception as e:
                    print(f"Error visiting playlist: {e}")
        
        # Remove duplicates (one final pass)
        unique_videos = []
        seen_urls = set()
        for video in videos:
            video_id = video["url"].split("v=")[1].split("&")[0] if "v=" in video["url"] else video["url"]
            if video_id not in seen_urls:
                seen_urls.add(video_id)
                unique_videos.append(video)
        
        videos = unique_videos
        print(f"Final video count after deduplication: {len(videos)}")
        
        await browser.close()
    
    return videos


def extract_date_from_title(title: str) -> str:
    """Helper function to extract and format date from video title"""
    # Look for date pattern at the end of the title (e.g., "Meeting - 05/29/2025")
    date_match = re.search(r'[-–—\s]+\s*(\d{1,2})/(\d{1,2})/(\d{2,4})\s*$', title)
    if date_match:
        month, day, year = date_match.groups()
        if len(year) == 2:
            year = f"20{year}"
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
    # Look for any MM/DD/YYYY pattern
    date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', title)
    if date_match:
        month, day, year = date_match.groups()
        if len(year) == 2:
            year = f"20{year}"
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
    # Try to match month name format (e.g., "February 18, 2025")
    month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?,\s+(\d{4})'
    month_match = re.search(month_pattern, title)
    if month_match:
        month_name, day, year = month_match.groups()
        month_dict = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        month_num = month_dict.get(month_name, '01')
        return f"{year}-{month_num}-{day.zfill(2)}"
        
    # Look for just a year (e.g., "2025")
    year_match = re.search(r'\b(20\d{2})\b', title)
    if year_match:
        year = year_match.group(1)
        return f"{year}-01-01"
        
    # Default to today's date if nothing found
    return datetime.now().strftime('%Y-%m-%d')


if __name__ == "__main__":
    # For testing this module individually
    import json
    
    async def test():
        results = await scrape_slc("https://www.youtube.com/@SLCLiveMeetings/streams")
        print(json.dumps(results, indent=2))
    
    asyncio.run(test())
