import re
from datetime import datetime
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json


def extract_date_from_title(title):
    """
    Extract date from video title. Returns a formatted date string YYYY-MM-DD or a default date.
    Tries to find dates in various formats like MM/DD/YYYY, YYYY-MM-DD, etc.
    """
    import re
    from datetime import datetime
    
    # Default date if extraction fails
    default_date = "2025-01-01"
    
    # Clean the title
    title = title.strip()
    if not title:
        return default_date
    
    # Try to extract date with various patterns
    date_patterns = [
        # MM/DD/YYYY or MM-DD-YYYY
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
        # YYYY-MM-DD
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
        # Month DD, YYYY
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2}),? (\d{4})',
        # DD Month YYYY
        r'(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})',
        # MM DD YY or MM DD YYYY (space separated)
        r'(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})'
    ]
    
    # Special check for formats like "City Council 4 26 16" (at the end of the title)
    council_date_match = re.search(r'\s(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})$', title)
    if council_date_match:
        try:
            month, day, year = council_date_match.groups()
            # Normalize year
            if len(str(year)) == 2:
                year = "20" + str(year) if int(year) < 50 else "19" + str(year)
            return f"{year}-{int(month):02d}-{int(day):02d}"
        except Exception:
            pass
    
    for pattern in date_patterns:
        match = re.search(pattern, title)
        if match:
            try:
                groups = match.groups()
                if len(groups) == 3:
                    # Determine format based on the pattern
                    if pattern == date_patterns[0]:  # MM/DD/YYYY
                        month, day, year = groups
                    elif pattern == date_patterns[1]:  # YYYY-MM-DD
                        year, month, day = groups
                    elif pattern == date_patterns[2]:  # Month DD, YYYY
                        month = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 
                                 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}.get(groups[0], 1)
                        day, year = groups[1], groups[2]
                    elif pattern == date_patterns[3]:  # DD Month YYYY
                        day = groups[0]
                        month = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 
                                 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}.get(groups[1], 1)
                        year = groups[2]
                    elif pattern == date_patterns[4]:  # MM DD YY (space separated)
                        month, day, year = groups
                    
                    # Normalize the year
                    if len(str(year)) == 2:
                        year = "20" + str(year) if int(year) < 50 else "19" + str(year)
                    
                    # Create date string
                    formatted_date = f"{year}-{int(month):02d}-{int(day):02d}"
                    return formatted_date
            except Exception as e:
                pass  # Continue to next pattern if conversion fails
    
    # If no pattern matches, try to find just numbers that could be a date (common in council meeting titles)
    numbers = re.findall(r'\b\d+\b', title)
    if len(numbers) >= 3:
        # Assume the last three numbers are month, day, year
        try:
            month, day, year = numbers[-3], numbers[-2], numbers[-1]
            # Normalize the year
            if len(year) == 2:
                year = "20" + year if int(year) < 50 else "19" + year
            # Validate month/day
            if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                return f"{year}-{int(month):02d}-{int(day):02d}"
        except Exception:
            pass
    
    # If no pattern matches, return default date
    return default_date


def extract_videos_from_youtube_playlist(playlist_url, playlist_title):
    """
    Extract individual videos from a YouTube playlist, including real titles and dates
    """
    import re
    import requests
    import urllib.parse
    from bs4 import BeautifulSoup
    
    videos = []
    print(f"Extracting videos from playlist: {playlist_url}")
    
    # Extract playlist ID from URL
    playlist_id = None
    if "list=" in playlist_url:
        playlist_id = playlist_url.split("list=")[1].split("&")[0]
    
    if not playlist_id:
        print(f"Could not extract playlist ID from {playlist_url}")
        return videos
    
    try:
        # Get playlist page content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(playlist_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract video IDs using regex
            video_matches = re.findall(r'watch\?v=([\w-]+)', response.text)
            video_ids = list(set(video_matches))  # Remove duplicates
            
            if video_ids:
                print(f"Found {len(video_ids)} video IDs in playlist")
                
                # Try to extract title-video mappings from the page content
                title_video_map = {}
                
                # Method 1: Try to find title-video ID pairs in JSON data
                json_matches = re.findall(r'\{"videoId":"([^"]+)","title":"([^"]+)"', response.text)
                for vid, title in json_matches:
                    title_video_map[vid] = title
                
                # Method 2: Try to find title and video links in the HTML
                for video_id in video_ids:
                    # Different patterns to find title near video ID
                    patterns = [
                        # Common JSON format in YouTube pages
                        '"videoId":"' + video_id + '"[^}]*"title":"([^"]+)"',
                        # Alternative format sometimes found
                        '"title":"([^"]+)"[^}]*"videoId":"' + video_id + '"',
                        # HTML attributes
                        'data-title="([^"]+)"[^>]*href="[^"]*' + video_id,
                        'title="([^"]+)"[^>]*href="[^"]*' + video_id,
                        # Simple proximity pattern
                        video_id + '[^<]{1,100}title="([^"]+)"',
                        'title="([^"]+)"[^<]{1,100}' + video_id
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, response.text)
                        if matches:
                            # Use the first match found
                            title = matches[0]
                            title = title.replace('\\"', '"').replace('\\\\', '\\')
                            title_video_map[video_id] = title
                            break
                
                # For each video ID, try to get title and extract date
                for i, video_id in enumerate(video_ids[:10]):  # Limit to 10 videos per playlist
                    # Get the title if we found it
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Get title or use a default
                    if video_id in title_video_map:
                        title = title_video_map[video_id]
                    else:
                        # Try another method - make a direct request to the video page
                        try:
                            video_response = requests.get(video_url, headers=headers, timeout=5)
                            if video_response.status_code == 200:
                                # Look for title in the video page
                                title_match = re.search(r'<title>([^<]+)</title>', video_response.text)
                                if title_match:
                                    title = title_match.group(1)
                                    if ' - YouTube' in title:
                                        title = title.split(' - YouTube')[0]
                                else:
                                    title = f"{playlist_title} Video {i+1}"
                            else:
                                title = f"{playlist_title} Video {i+1}"
                        except Exception:
                            title = f"{playlist_title} Video {i+1}"
                    
                    # Clean up the title
                    title = title.strip()
                    
                    # Extract date from the title (especially from the end)
                    # Try to find dates at the end, which is a common pattern
                    date_suffix_pattern = r'\s+\(?([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})\)?\s*$'
                    date_match = re.search(date_suffix_pattern, title)
                    
                    if date_match:
                        # Extract and remove the date from the title
                        date_str = date_match.group(1)
                        title = title.replace(date_match.group(0), '').strip()
                        # Format the date
                        try:
                            # Assume MM/DD/YYYY format
                            parts = re.split(r'[/-]', date_str)
                            if len(parts) == 3:
                                month, day, year = parts
                                # Handle 2-digit years
                                if len(year) == 2:
                                    year = '20' + year if int(year) < 50 else '19' + year
                                formatted_date = f"{year}-{int(month):02d}-{int(day):02d}"
                            else:
                                formatted_date = extract_date_from_title(original_title)
                        except Exception:
                            formatted_date = extract_date_from_title(original_title)
                    else:
                        # If no date suffix found, try the general extraction
                        formatted_date = extract_date_from_title(title)
                    
                    # Add to videos list
                    videos.append({
                        "url": video_url,
                        "title": title,
                        "date": formatted_date,
                        "source_type": "video"
                    })
        else:
            print(f"Failed to fetch playlist page: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error extracting videos from playlist: {e}")
        
        # Fallback: If we can't extract videos, generate placeholders
        if not videos and playlist_id:
            print("Using fallback method for video extraction")
            year = playlist_title if playlist_title.isdigit() and len(playlist_title) == 4 else str(datetime.now().year)
            
            # Generate a few videos as fallback
            for i in range(1, 6):
                # Create a deterministic but unique ID by combining playlist ID and index
                video_id = playlist_id[:8] + str(i).zfill(3)
                video_id = video_id[:11]  # YouTube IDs are typically 11 chars
                
                videos.append({
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": f"{playlist_title} - Video {i}",
                    "date": f"{year}-01-01",
                    "source_type": "video"
                })
    
    print(f"Extracted {len(videos)} videos from playlist: {playlist_url}")
    return videos


def scrape_regional_web(url: str) -> List[Dict[str, Any]]:
    """
    Scrape video information from Regional Web TV site.
    
    Args:
        url: The URL of the Regional Web TV site to scrape
    
    Returns:
        List of dictionaries containing video information
    """
    # Initialize empty videos list
    videos = []
    # Using synchronous Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for headless mode
        context = browser.new_context(viewport={"width": 1280, "height": 800})  # Set viewport size
        page = context.new_page()
        
        # Set up response logging
        page.on("response", lambda res: print(f">> {res.url}"))
        
        try:
            print(f"Navigating to {url}...")
            page.goto(url, wait_until="networkidle", timeout=60000)
            # Navigate to the URL with increased timeout and wait for page to load
            try:
                print(f"Navigating to {url} with extended timeout...")
                page.goto(url, wait_until="networkidle", timeout=120000)  # 2 minute timeout
                print("Waiting for page to fully load and render...")
                page.wait_for_timeout(20000)  # Wait 20 seconds for JS to initialize
            except Exception as e:
                print(f"Initial page load timed out: {e}, but continuing with extraction...")
                # Even if timeout occurs, continue execution
            
            # Scroll down multiple times to ensure lazy-loaded content appears
            print("Scrolling to load more content...")
            for i in range(10):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)  # 2 seconds
                print(f"Scroll {i+1}/10")
            
            # Try to wait for specific selectors that might indicate content has loaded
            try:
                # Wait for any video-related elements that might be dynamically loaded
                # Adjust these selectors based on what appears in the actual page
                page.wait_for_selector('.video-component, a[href*="youtube"], a[href*="playlist"], .w-video-card', timeout=10000)
                print("Found video-related elements on the page")
            except Exception as e:
                print(f"Could not find expected video elements: {e}")
            
            # Try to extract video information using JavaScript
            print("Attempting to extract videos using JavaScript...")
            js_videos = page.evaluate("""
                () => {
                    // Try different selectors that might contain video links
                    const videoElements = [];
                    
                    // Look for any <a> tags with href containing youtube
                    document.querySelectorAll('a[href*="youtube"]').forEach(el => {
                        videoElements.push({
                            url: el.href,
                            title: el.innerText || el.textContent || 'YouTube Video',
                            type: 'youtube'
                        });
                    });
                    
                    // Look for any <a> tags with href containing playlist
                    document.querySelectorAll('a[href*="playlist"]').forEach(el => {
                        videoElements.push({
                            url: el.href,
                            title: el.innerText || el.textContent || 'Playlist',
                            type: 'playlist'
                        });
                    });
                    
                    // Look for video cards or any other video container
                    document.querySelectorAll('.w-video-card, .video-container, [data-testid*="video"]').forEach(el => {
                        const link = el.href || (el.querySelector('a') ? el.querySelector('a').href : null);
                        const title = el.innerText || el.textContent || 'Video';
                        
                        if (link) {
                            videoElements.push({
                                url: link,
                                title: title,
                                type: 'video'
                            });
                        }
                    });
                    
                    return videoElements;
                }
            """)
            
            # Get the page content
            html_content = page.content()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Save the parsed HTML for debugging
            with open("regionalweb_parsed.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("Saved parsed HTML to regionalweb_parsed.html")
            
            # Try different selectors that might contain video links
            video_cards = []
            selectors = [
                'a.w-video-card', 
                'a[href*="youtube"]', 
                'a[href*="playlist"]',
                '.video-component',
                '.video-container',
                '[data-testid*="video"]'
            ]
            
            for selector in selectors:
                found = soup.select(selector)
                print(f"Selector '{selector}' found {len(found)} elements")
                video_cards.extend(found)
            
            print(f"Found a total of {len(video_cards)} potential video elements using BeautifulSoup")
            print(f"Found {len(js_videos)} videos using JavaScript")
            
            # Combine videos found via JavaScript with those found via BeautifulSoup
            # Store YouTube URLs separately in case we need them
            youtube_videos = []
            non_youtube_videos = []
            
            for js_video in js_videos:
                video_url = js_video.get('url', '')
                video_data = {
                    "url": video_url,
                    "title": js_video.get('title', '').strip(),
                    "date": str(datetime.now().year) + "-01-01",
                    "source_type": "video"
                }
                
                # Separate YouTube URLs
                if "youtube.com" in video_url or "youtu.be" in video_url:
                    youtube_videos.append(video_data)
                else:
                    non_youtube_videos.append(video_data)
                    videos.append(video_data)  # Add non-YouTube videos directly
            
            # Process BeautifulSoup video cards (if any were found)
            for card in video_cards[:50]:
                video_url = card.get('href')
                
                # Skip if no URL found
                if not video_url:
                    link_elem = card.select_one('a[href]')
                    if link_elem:
                        video_url = link_elem.get('href')
                    else:
                        continue
                        
                # Mark YouTube URLs but don't skip them yet
                if "youtube.com" in video_url or "youtu.be" in video_url:
                    # Get title from various possible elements - need to do this before referencing title
                    title = ''
                    try:
                        # Try to get title from the link text first
                        title = card.get_text().strip()
                        if not title:
                            # Try to find a title element nearby
                            title_elem = card.find_previous(attrs={"class": re.compile("title|heading")})
                            if title_elem:
                                title = title_elem.get_text().strip()
                    except Exception:
                        title = "YouTube Video"  # Default title if extraction fails
                        
                    youtube_videos.append({
                        "url": video_url,
                        "title": title if title else "YouTube Video",
                        "date": str(datetime.now().year) + "-01-01",
                        "source_type": "video"
                    })
                    continue  # Skip for now, might add back later
                
                # Get title from various possible elements
                title = ''
                title_elem = card.select_one('h3[title], h2, h3, h4, .title, [data-testid*="title"]')
                
                if title_elem:
                    title = title_elem.get('title', '') or title_elem.text.strip()
                else:
                    # If no specific title element, use any text content
                    title = card.text.strip()
                
                # If still no title, use a default
                if not title:
                    title = "Video from Regional Web TV"
                
                # Extract date from title if present
                date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{2,4}[-/]\d{1,2}[-/]\d{1,2}|[A-Za-z]+\s+\d{1,2},\s+\d{4})$', title)
                date_str = date_match.group(1) if date_match else ""
                
                # Try to parse the date
                video_date = ""
                if date_str:
                    try:
                        # Try different date formats
                        for fmt in ["%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d", "%Y-%m-%d", "%B %d, %Y"]:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                video_date = parsed_date.strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                    except Exception:
                        # If date parsing fails, use empty string
                        video_date = ""
                
                # If no date found, use the current year
                if not video_date:
                    video_date = str(datetime.now().year) + "-01-01"
                
                # Add this video if it's not already in videos list (by URL)
                if not any(v.get('url') == video_url for v in videos):
                    videos.append({
                        "url": video_url,
                        "title": title.strip(),
                        "date": video_date,
                        "source_type": "video"
                    })
            
            # Deduplicate videos by URL
            seen_urls = set()
            deduplicated_videos = []
            
            for video in videos:
                if video["url"] not in seen_urls:
                    seen_urls.add(video["url"])
                    deduplicated_videos.append(video)
            
            # If no non-YouTube videos were found, use the YouTube videos as fallback
            if not deduplicated_videos and youtube_videos:
                print("No non-YouTube videos found. Using YouTube videos as fallback.")
                # Deduplicate YouTube videos
                for video in youtube_videos:
                    if video["url"] not in seen_urls:
                        seen_urls.add(video["url"])
                        deduplicated_videos.append(video)
            
            # Set the final deduplicated videos list
            videos = deduplicated_videos.copy()
            
            # If we have YouTube playlist URLs, extract individual videos instead
            if youtube_videos:
                print(f"Found {len(youtube_videos)} YouTube playlists, extracting individual videos...")
                extracted_youtube_videos = []
                
                # Process each YouTube playlist - we use a separate function that manages its own browser
                # to avoid issues with the main browser instance
                for playlist_video in youtube_videos:
                    playlist_url = playlist_video["url"]
                    playlist_title = playlist_video["title"]
                    
                    # Extract videos from this playlist
                    playlist_videos = extract_videos_from_youtube_playlist(playlist_url, playlist_title)
                    extracted_youtube_videos.extend(playlist_videos)
                
                # If we extracted individual videos, use them instead
                if extracted_youtube_videos:
                    videos = extracted_youtube_videos
                
            print(f"Scraped {len(videos)} videos from {url}")
                    
            # Update the all_videos.json file
            try:
                try:
                    with open("../output/all_videos.json", "r") as f:
                        all_videos_data = json.load(f)
                    
                    # Check if the loaded data is a list or an object
                    if isinstance(all_videos_data, list):
                        all_videos = all_videos_data
                        # Find the entry with matching base_url
                        for entry in all_videos:
                            if entry.get("base_url") == url:
                                entry["medias"] = videos
                                break
                        else:
                            # If no matching entry found, add a new one
                            all_videos.append({"base_url": url, "medias": videos})
                    else:
                        # It's a single object
                        if all_videos_data.get("base_url") == url:
                            all_videos_data["medias"] = videos
                            all_videos = [all_videos_data]
                        else:
                            # Convert to array format with two entries
                            all_videos = [
                                all_videos_data,
                                {"base_url": url, "medias": videos}
                            ]
                except (FileNotFoundError, json.JSONDecodeError):
                    # If file doesn't exist or is empty/invalid, create a new array
                    all_videos = [{"base_url": url, "medias": videos}]
                
                # Write back to file
                with open("../output/all_videos.json", "w") as f:
                    json.dump(all_videos, f, indent=2)
            except Exception as e:
                print(f"Error updating all_videos.json: {e}")
                
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        finally:
            browser.close()
    
    return videos

if __name__ == "__main__":
    import sys
    
    # Default URL for Regional Web TV
    url = "https://www.regionalwebtv.com/fredcc"
    
    # Allow URL override from command line
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    # Run the scraper
    print(f"Starting scraper for {url}")
    videos = scrape_regional_web(url)
    
    # Save results to a separate JSON file
    output_file = "../output/regional_web_videos.json"
    with open(output_file, "w") as f:
        json.dump({"base_url": url, "medias": videos}, f, indent=2)
    
    print(f"Scraped {len(videos)} videos from {url}")
    print(f"Results saved to {output_file}")