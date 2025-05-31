"""
Scraper for Lansdale.org civic media videos
"""
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import re
import time

# Process more videos to ensure we get a good sample
TARGET_VIDEOS = 100  # Process a reasonable number of videos

async def scrape_lansdale(url):
    """
    Scrape video URLs from Lansdale website.
    
    Args:
        url: The URL of the Lansdale page
        
    Returns:
        List of dictionaries containing video URLs and metadata
    """
    print(f"Starting to scrape videos from: {url}")
    video_urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # Navigate to the Lansdale.org page with a more reliable waiting strategy
            await page.goto(url, timeout=30000, wait_until='domcontentloaded')
            # Wait for a reasonable time for content to load instead of networkidle
            await page.wait_for_timeout(5000)
            print("Page loaded")
            
            # Get all links from the page
            all_links = await page.query_selector_all('a')
            print(f"Found {len(all_links)} total links on the page")
            
            # Filter for links containing VID= which are actual video links
            for link in all_links:
                try:
                    href = await link.get_attribute('href')
                    if href and 'VID=' in href:
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            video_url = f"https://www.lansdale.org{href}"
                        else:
                            video_url = href
                        
                        if video_url not in video_urls:
                            video_urls.append(video_url)
                            print(f"Found video URL: {video_url}")
                except Exception as e:
                    continue
            
            # If we don't find any links with VID=, try looking for other potential video links
            if not video_urls:
                print("No VID= links found. Checking page content...")
                content = await page.content()
                vid_urls = re.findall(r'href=["\'](.*?VID=.*?)["\'\#]', content)
                
                for url_part in vid_urls:
                    if url_part.startswith('/'):
                        full_url = f"https://www.lansdale.org{url_part}"
                    elif not url_part.startswith('http'):
                        full_url = f"https://www.lansdale.org/{url_part}"
                    else:
                        full_url = url_part
                        
                    if full_url not in video_urls:
                        video_urls.append(full_url)
                        print(f"Found video URL from content: {full_url}")
                        
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await browser.close()
    
    print(f"Found {len(video_urls)} unique videos")
    
    # Limit the number of videos to process
    if len(video_urls) > TARGET_VIDEOS:
        video_urls = video_urls[:TARGET_VIDEOS]
    
    print(f"Will process {len(video_urls)} videos")
    
    # Process videos and collect metadata
    result = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        )
        
        # Process each video one by one to ensure reliability
        for i, url in enumerate(video_urls):
            page = await context.new_page()
            try:
                # Get video information
                video_info = await get_video_info(url, page)
                
                if video_info:
                    result.append(video_info)
                    print(f"Added: {video_info['title']} ({video_info['date']})")
                
                print(f"Processed {i+1}/{len(video_urls)} videos")
            finally:
                await page.close()
                # Add a small delay to avoid rate limiting
                await asyncio.sleep(1)
        
        await browser.close()
    
    # Sort the videos by date (newest first)
    result = sorted(result, key=lambda x: x["date"], reverse=True)
    
    return result

async def get_video_info(url, page):
    print(f"Processing: {url}")
    try:
        # Navigate to the video page
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        
        # Wait for the necessary elements to load
        await asyncio.sleep(2)  # Give the page a moment to stabilize
        
        # Page loaded successfully
        print(f"Video page loaded: {url}")
        
        # Extract video ID from URL if present
        video_id = None
        vid_match = re.search(r'VID=([^&#]+)', url)
        if vid_match:
            video_id = vid_match.group(1)
            print(f"Video ID: {video_id}")
        
        # Get video title
        title = None
        
        # Try to get title from the page
        title_selectors = [
            'h1', 
            '.mediaTitle', 
            '.video-title', 
            '.title', 
            '.content-title',
            'title'
        ]
        
        for selector in title_selectors:
            try:
                if selector == 'title':
                    title = await page.title()
                else:
                    element = await page.query_selector(selector)
                    if element:
                        title = await element.text_content()
                if title and title.strip() and title != "Lansdale, PA - Official Website":
                    break
            except Exception as e:
                print(f"Error getting title with selector {selector}: {e}")
                continue
        
        # If title not found, use video ID or URL
        if not title or title == "Lansdale, PA - Official Website":
            if video_id:
                # Format the video ID into a readable title
                title = video_id.replace('-', ' ').title()
                title = f"Lansdale Council - {title}"
            else:
                # Extract from URL
                path_part = url.split('/')[-1]
                if '?' in path_part:
                    path_part = path_part.split('?')[0]
                title = path_part.replace('-', ' ').replace('_', ' ').title()
                title = f"Lansdale Council Meeting - {title}"
        
        # Extract the actual upload date
        upload_date = None
        
        # Print the page text for debugging
        page_text = await page.evaluate('document.body.innerText')
        print("\nPage text sample:")
        text_sample = page_text[:500] + ("..." if len(page_text) > 500 else "")
        print(text_sample)
        
        # First, look for specific date elements that might contain the upload date
        date_selectors = [
            # Common date containers
            '.date-display', '.video-date', '.media-date', '.upload-date',
            '.publication-date', '.published-date', '.timestamp',
            # Text elements that might contain date information
            '.content p:has-text("Date:")', 'span:has-text("Date:")',
            'div:has-text("Date:")', 'p:has-text("Date:")',
            'div.field-label:has-text("Date")', '.meta-data', '.video-meta',
            # Generic containers that might have date information
            '.content-meta', '.video-info', '.media-info'
        ]
        
        for selector in date_selectors:
            try:
                elements = await page.query_selector_all(selector)
                print(f"Found {len(elements)} elements with selector '{selector}'")
                
                for element in elements:
                    try:
                        date_text = await element.text_content()
                        print(f"Date element text: {date_text}")
                        
                        # Look for MM/DD/YYYY pattern
                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', date_text)
                        if date_match:
                            date_str = date_match.group(1)
                            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                            upload_date = date_obj.strftime("%Y-%m-%d")
                            print(f"Found date: {upload_date}")
                            break
                            
                        # Look for Month DD, YYYY pattern
                        month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?[,]?\s+(\d{4})'
                        month_match = re.search(month_pattern, date_text, re.IGNORECASE)
                        if month_match:
                            month = month_match.group(1)
                            day = month_match.group(2)
                            year = month_match.group(3)
                            date_str = f"{month} {day}, {year}"
                            date_obj = datetime.strptime(date_str, "%B %d, %Y")
                            upload_date = date_obj.strftime("%Y-%m-%d")
                            print(f"Found date: {upload_date}")
                            break
                    except Exception as e:
                        print(f"Error processing date element: {e}")
                        continue
                
                if upload_date:
                    break
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue
        
        # If date not found in specific elements, search the entire page text
        if not upload_date:
            print("Searching entire page text for dates...")
            
            # Look for pattern like "Date: MM/DD/YYYY" or "Uploaded: MM/DD/YYYY"
            date_label_patterns = [
                r'Date:\s*(\d{1,2}/\d{1,2}/\d{4})',
                r'Uploaded:\s*(\d{1,2}/\d{1,2}/\d{4})',
                r'Published:\s*(\d{1,2}/\d{1,2}/\d{4})',
                r'Posted:\s*(\d{1,2}/\d{1,2}/\d{4})'
            ]
            
            for pattern in date_label_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    try:
                        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                        upload_date = date_obj.strftime("%Y-%m-%d")
                        print(f"Found date with label pattern: {upload_date}")
                        break
                    except Exception as e:
                        print(f"Error parsing date: {e}")
            
            # If still no date, look for any date format in the page content
            if not upload_date:
                # MM/DD/YYYY format
                date_matches = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', page_text)
                for date_str in date_matches:
                    try:
                        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                        # Only use dates that are reasonably recent (within last 2 years)
                        delta = datetime.now() - date_obj
                        if delta.days < 730:  # Roughly 2 years
                            upload_date = date_obj.strftime("%Y-%m-%d")
                            print(f"Found date in page text: {upload_date}")
                            break
                    except Exception as e:
                        print(f"Error parsing date: {e}")
                
                # If still no date, try Month DD, YYYY format
                if not upload_date:
                    month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?[,]?\s+(\d{4})'
                    month_matches = re.findall(month_pattern, page_text, re.IGNORECASE)
                    for match in month_matches:
                        try:
                            month, day, year = match
                            date_str = f"{month} {day}, {year}"
                            date_obj = datetime.strptime(date_str, "%B %d, %Y")
                            # Only use dates that are reasonably recent
                            delta = datetime.now() - date_obj
                            if delta.days < 730:  # Roughly 2 years
                                upload_date = date_obj.strftime("%Y-%m-%d")
                                print(f"Found month format date in page text: {upload_date}")
                                break
                        except Exception as e:
                            print(f"Error parsing month format date: {e}")
        
        # If all the above methods fail, try to extract date from video ID as fallback
        if not upload_date and video_id:
            print("Extracting date from video ID as fallback...")
            
            # Try to extract numeric date from video ID (like 10022024 for October 2, 2024)
            numeric_date_match = re.search(r'(\d{1,2})(\d{1,2})(202\d)', video_id)
            if numeric_date_match:
                try:
                    month = numeric_date_match.group(1)
                    day = numeric_date_match.group(2)
                    year = numeric_date_match.group(3)
                    date_obj = datetime.strptime(f"{month}/{day}/{year}", "%m/%d/%Y")
                    upload_date = date_obj.strftime("%Y-%m-%d")
                    print(f"Extracted date from video ID numeric pattern: {upload_date}")
                except Exception as e:
                    print(f"Error parsing numeric date from video ID: {e}")
            
            # Try month name patterns
            if not upload_date:
                month_names = {
                    'january': '01', 'february': '02', 'march': '03', 'april': '04',
                    'may': '05', 'june': '06', 'july': '07', 'august': '08',
                    'september': '09', 'october': '10', 'november': '11', 'december': '12'
                }
                
                for month_name, month_num in month_names.items():
                    if month_name.lower() in video_id.lower():
                        # Extract year if present
                        year_match = re.search(r'\b(202\d)\b', video_id)
                        year = year_match.group(1) if year_match else "2024"  # Default to 2024 if no year found
                        
                        # Extract day if present
                        day_match = re.search(r'\b(\d{1,2})\b', video_id)
                        if day_match:
                            day = day_match.group(1).zfill(2)
                            upload_date = f"{year}-{month_num}-{day}"
                            print(f"Extracted date from video ID with month name: {upload_date}")
                            break
        
        # If all extraction methods fail, use the current month/year with a day from the video ID if possible
        if not upload_date:
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            # Try to extract a day number from video ID
            day = "15"  # Default to middle of month
            day_match = re.search(r'\b(\d{1,2})\b', video_id if video_id else "")
            if day_match:
                day_num = int(day_match.group(1))
                if 1 <= day_num <= 31:
                    day = str(day_num).zfill(2)
            
            month_str = str(current_month).zfill(2)
            upload_date = f"{current_year}-{month_str}-{day}"
            print(f"Using fallback date based on current month/year: {upload_date}")
        
        # Return the metadata
        return {
            "url": url,
            "title": title.strip(),
            "date": upload_date,
            "source_type": "video"
        }
            
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

if __name__ == "__main__":
    # For testing this module individually
    import json
    
    async def test():
        results = await scrape_lansdale("https://www.lansdale.org/CivicMedia?CID=2024-Council-Meetings-26")
        print(json.dumps(results, indent=2))
    
    asyncio.run(test())
