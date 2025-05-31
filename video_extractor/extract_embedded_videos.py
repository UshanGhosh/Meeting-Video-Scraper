#!/usr/bin/env python3
"""
Embedded Video Extractor and yt-dlp Tester

This script:
1. Takes webpage URLs with embedded video players
2. Visits the webpage
3. Locates and extracts downloadable video source URLs
4. Verifies that they work with yt-dlp
"""

import json
import re
import logging
import requests
from bs4 import BeautifulSoup
import time
import random
import subprocess
import json
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("embedded_video_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# List of URLs to test
TEST_URLS = [
    "https://video.ibm.com/recorded/134312408",
    "https://monticello.viebit.com/watch?hash=HCZTN4vuyJ91LlrS",
    "https://play.champds.com/guilderlandny/event/431"
]

# Common video file extensions
VIDEO_EXTENSIONS = ['mp4', 'webm', 'mov', 'avi', 'wmv', 'flv', 'm3u8', 'mpd', 'ts']

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

def is_downloadable_with_ytdlp(url):
    """
    Check if a URL is downloadable with yt-dlp.
    Returns a tuple of (url, is_downloadable, error_message)
    """
    try:
        logger.info(f"Testing URL with yt-dlp: {url}")
        
        # Import here to avoid dependency issues
        try:
            from yt_dlp import YoutubeDL
            
            ydl_opts = {
                'quiet': True,
                'simulate': True,
                'no_warnings': False,
                'skip_download': True,
                'no_color': True,
                'noprogress': True,
                'verbose': False,
                'format': 'best'
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return url, True, None
        except ImportError as ie:
            logger.error(f"Import error: {ie}")
            
            # Fallback to subprocess
            try:
                # Try subprocess call instead
                result = subprocess.run(
                    ["python", "-m", "yt_dlp", "--simulate", "--quiet", url],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return url, True, None
                else:
                    return url, False, result.stderr
            except subprocess.SubprocessError as se:
                return url, False, f"Subprocess error: {se}"
        except Exception as e:
            return url, False, str(e)
    except Exception as e:
        logger.error(f"Error checking URL with yt-dlp: {url}, {str(e)}")
        return url, False, str(e)

def extract_video_urls_from_page(page_url):
    """
    Extracts potential video URLs from a webpage by:
    1. Looking for <video> tags
    2. Looking for <iframe> sources
    3. Finding video URLs in JavaScript/JSON data
    4. Looking for download links
    5. Looking for HLS (.m3u8) or DASH (.mpd) manifests
    
    Returns a list of potential video URLs.
    """
    logger.info(f"Extracting video URLs from: {page_url}")
    
    try:
        # Make request to the webpage
        response = requests.get(page_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = response.url
        potential_urls = []
        
        # 1. Extract URLs from <video> tags
        logger.info("Looking for <video> tags...")
        for video in soup.find_all('video'):
            # Check src attribute
            if video.get('src'):
                video_url = urljoin(base_url, video['src'])
                potential_urls.append(video_url)
                logger.info(f"Found video src: {video_url}")
            
            # Check source tags inside video
            for source in video.find_all('source'):
                if source.get('src'):
                    source_url = urljoin(base_url, source['src'])
                    potential_urls.append(source_url)
                    logger.info(f"Found video source: {source_url}")
        
        # 2. Extract URLs from <iframe> sources (embedded players)
        logger.info("Looking for <iframe> sources...")
        for iframe in soup.find_all('iframe'):
            if iframe.get('src'):
                iframe_url = urljoin(base_url, iframe['src'])
                logger.info(f"Found iframe: {iframe_url}")
                potential_urls.append(iframe_url)
                
                # Optionally, we could recursively check iframe content
                # This would require additional requests to the iframe sources
        
        # 3. Extract video URLs from JSON data in scripts
        logger.info("Looking for video URLs in JSON/JavaScript...")
        json_pattern = r'(\"|\')(?:url|src|source|file|videoUrl|videoSrc)(\"|\')\s*:\s*(\"|\')([^\"\']+\.(mp4|webm|m3u8|mpd))(\"|\')' 
        for script in soup.find_all('script'):
            if script.string:
                matches = re.findall(json_pattern, script.string, re.IGNORECASE)
                for match in matches:
                    video_url = match[3] + match[4]  # URL + extension
                    if not video_url.startswith(('http://', 'https://')):
                        video_url = urljoin(base_url, video_url)
                    potential_urls.append(video_url)
                    logger.info(f"Found video URL in script: {video_url}")
        
        # 4. Look for direct links to video files
        logger.info("Looking for direct links to video files...")
        for extension in VIDEO_EXTENSIONS:
            pattern = f'["\']([^"\']*\\.{extension}(\\?[^"\']*)?)["\']'
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            for match in matches:
                video_url = match[0]
                if not video_url.startswith(('http://', 'https://')):
                    video_url = urljoin(base_url, video_url)
                potential_urls.append(video_url)
                logger.info(f"Found direct video link: {video_url}")
        
        # 5. Look for download buttons/links
        logger.info("Looking for download links...")
        download_keywords = ['download', 'media', 'video']
        for a in soup.find_all('a'):
            if a.get('href') and any(keyword in a.get('href', '').lower() for keyword in download_keywords):
                download_url = urljoin(base_url, a['href'])
                potential_urls.append(download_url)
                logger.info(f"Found download link: {download_url}")
            
            # Also check link text
            if a.text and any(keyword in a.text.lower() for keyword in download_keywords):
                download_url = urljoin(base_url, a.get('href', ''))
                potential_urls.append(download_url)
                logger.info(f"Found download link (by text): {download_url}")
        
        # Remove duplicates and return
        return list(set(potential_urls))
    
    except Exception as e:
        logger.error(f"Error extracting video URLs from {page_url}: {str(e)}")
        return []

def process_url(url):
    """Process a single URL, extract embedded videos, and test with yt-dlp."""
    results = {
        "original_url": url,
        "direct_downloadable": False,
        "embedded_videos_found": [],
        "downloadable_videos": [],
        "errors": []
    }
    
    # First, check if the original URL is directly downloadable
    logger.info(f"Checking if URL is directly downloadable: {url}")
    direct_url, is_direct_downloadable, direct_error = is_downloadable_with_ytdlp(url)
    
    if is_direct_downloadable:
        results["direct_downloadable"] = True
        results["downloadable_videos"].append(direct_url)
        logger.info(f"URL is directly downloadable: {url}")
        return results
    
    if direct_error:
        results["errors"].append(f"Direct URL error: {direct_error}")
    
    # If not directly downloadable, extract embedded video URLs
    logger.info(f"Extracting embedded videos from: {url}")
    embedded_videos = extract_video_urls_from_page(url)
    results["embedded_videos_found"] = embedded_videos
    
    # Test each embedded video URL
    for video_url in embedded_videos:
        logger.info(f"Testing embedded video URL: {video_url}")
        embedded_url, is_embedded_downloadable, embedded_error = is_downloadable_with_ytdlp(video_url)
        
        if is_embedded_downloadable:
            results["downloadable_videos"].append(embedded_url)
            logger.info(f"Found downloadable embedded video: {embedded_url}")
        elif embedded_error:
            results["errors"].append(f"Embedded URL error ({embedded_url}): {embedded_error}")
    
    return results

def main():
    """Main function to test URLs and save results."""
    all_results = []
    output_file = "embedded_video_test_results.json"
    
    logger.info(f"Starting embedded video extraction and testing for {len(TEST_URLS)} URLs")
    
    # Process each URL
    for url in TEST_URLS:
        logger.info(f"Processing URL: {url}")
        result = process_url(url)
        all_results.append(result)
        
        # Add a small delay to avoid rate limiting
        time.sleep(2)
    
    # Format and save results
    formatted_results = {
        "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_urls_tested": len(TEST_URLS),
        "total_downloadable_videos_found": sum(len(r["downloadable_videos"]) for r in all_results),
        "results": all_results
    }
    
    # Save to JSON file
    try:
        with open(output_file, 'w') as file:
            json.dump(formatted_results, file, indent=2)
        logger.info(f"Successfully saved results to {output_file}")
    except Exception as e:
        logger.error(f"Error saving results to {output_file}: {str(e)}")
    
    # Print summary
    print("\n===== RESULTS SUMMARY =====")
    print(f"Total URLs tested: {len(TEST_URLS)}")
    print(f"Total downloadable videos found: {formatted_results['total_downloadable_videos_found']}")
    
    for result in all_results:
        print(f"\nOriginal URL: {result['original_url']}")
        print(f"Directly downloadable: {result['direct_downloadable']}")
        print(f"Embedded videos found: {len(result['embedded_videos_found'])}")
        print(f"Downloadable videos: {len(result['downloadable_videos'])}")
        if result['downloadable_videos']:
            print("Downloadable video URLs:")
            for url in result['downloadable_videos']:
                print(f"  - {url}")
    
    print(f"\nFull results saved to {output_file}")

if __name__ == "__main__":
    main()
