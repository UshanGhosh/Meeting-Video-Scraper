#!/usr/bin/env python3
"""
Video URL Extractor

This script extracts direct video URLs from meeting pages that can be downloaded using yt-dlp.
"""

import json
import os
import subprocess
import requests
from bs4 import BeautifulSoup
import re
import time
import sys
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("video_extractor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_json_file(file_path):
    """Load JSON data from file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return []

def save_json_file(data, file_path):
    """Save JSON data to file."""
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)
        logger.info(f"Successfully saved data to {file_path}")
    except Exception as e:
        logger.error(f"Error saving JSON file {file_path}: {e}")

def is_downloadable_with_ytdlp(url):
    """Check if a URL is downloadable with yt-dlp."""
    try:
        logger.info(f"Testing URL with yt-dlp: {url}")
        # Use Python module directly instead of subprocess
        try:
            # Import here to avoid dependency issues
            from yt_dlp import YoutubeDL
            
            ydl_opts = {
                'quiet': True,
                'simulate': True,
                'no_warnings': True,
                'skip_download': True,
                'no_color': True,
                'noprogress': True
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info is not None
        except ImportError:
            # Fallback to subprocess if module can't be imported
            logger.warning("Using fallback subprocess method for yt-dlp")
            result = subprocess.run(
                [sys.executable, "-m", "yt_dlp", "--simulate", url],
                capture_output=True, 
                text=True,
                timeout=60
            )
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.warning(f"yt-dlp check timed out for URL: {url}")
        return False
    except Exception as e:
        logger.error(f"Error checking URL with yt-dlp: {url}, {str(e)}")
        return False

def extract_video_url_from_webpage(page_url):
    """
    Visit a webpage and extract video source URLs that might be embedded.
    Returns a list of potential video URLs found.
    """
    try:
        logger.info(f"Extracting video URLs from webpage: {page_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(page_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        potential_urls = []
        
        # Look for common video elements
        # 1. Check for video tags
        for video in soup.find_all('video'):
            if video.get('src'):
                potential_urls.append(urljoin(page_url, video['src']))
            for source in video.find_all('source'):
                if source.get('src'):
                    potential_urls.append(urljoin(page_url, source['src']))
        
        # 2. Check for iframe embeds (YouTube, Vimeo, etc.)
        for iframe in soup.find_all('iframe'):
            if iframe.get('src'):
                potential_urls.append(iframe['src'])
        
        # 3. Look for JSON data that might contain video URLs
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                json_content = json.loads(script.string)
                # Extract URLs from JSON content (implementation depends on site structure)
                urls = extract_urls_from_json(json_content)
                potential_urls.extend(urls)
            except:
                pass
                
        # 4. Look for specific patterns in the HTML that might be video URLs
        # This regex looks for URLs ending with common video extensions
        video_extensions = r'https?://[^\s"\']+\.(mp4|mov|avi|wmv|flv|webm|m3u8|mpd)[\s"\']'
        for match in re.finditer(video_extensions, response.text):
            url = match.group(0).strip('\'"')
            potential_urls.append(url)
            
        # 5. Look for specific download links
        download_links = soup.find_all('a', href=True)
        for link in download_links:
            href = link['href']
            text = link.get_text().lower()
            if 'download' in href or 'download' in text or 'video' in text:
                potential_urls.append(urljoin(page_url, href))
                
        logger.info(f"Found {len(potential_urls)} potential video URLs on page")
        return list(set(potential_urls))  # Remove duplicates
    except Exception as e:
        logger.error(f"Error extracting video URL from webpage {page_url}: {e}")
        return []

def extract_urls_from_json(json_data, urls=None):
    """Recursively extract URLs from JSON data."""
    if urls is None:
        urls = []
    
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            if key in ['url', 'src', 'source', 'videoUrl', 'video_url', 'media', 'mediaUrl'] and isinstance(value, str):
                if value.startswith('http'):
                    urls.append(value)
            else:
                extract_urls_from_json(value, urls)
    elif isinstance(json_data, list):
        for item in json_data:
            extract_urls_from_json(item, urls)
            
    return urls

def process_url(url):
    """Process a single URL to find a downloadable video URL."""
    # First check if the URL is directly downloadable
    if is_downloadable_with_ytdlp(url):
        logger.info(f"URL is directly downloadable: {url}")
        return url
    
    # If not, try to extract video URLs from the webpage
    logger.info(f"URL is not directly downloadable, extracting embedded videos: {url}")
    potential_video_urls = extract_video_url_from_webpage(url)
    
    # Check each potential URL with yt-dlp
    for video_url in potential_video_urls:
        if is_downloadable_with_ytdlp(video_url):
            logger.info(f"Found downloadable video URL: {video_url}")
            return video_url
    
    logger.warning(f"No downloadable video URL found for: {url}")
    return None

def main():
    """Main function to extract and verify video URLs."""
    input_file = "../output/filtered_videos.json"
    output_file = "downloadable_videos.json"
    
    logger.info(f"Starting video URL extraction process")
    
    # Load the input JSON file
    video_data = load_json_file(input_file)
    
    # Create a sample input list and downloadable URLs list
    sample_input = []
    downloadable_urls = []
    
    # Process each site's media URLs
    for site_data in video_data:
        base_url = site_data.get("base_url", "")
        logger.info(f"Processing media from: {base_url}")
        
        for media in site_data.get("medias", []):
            url = media.get("url", "")
            if not url:
                continue
                
            # Add to sample input
            sample_input.append({
                "url": url,
                "title": media.get("title", ""),
                "date": media.get("date", ""),
                "source_type": media.get("source_type", "")
            })
            
            # Process the URL
            downloadable_url = process_url(url)
            if downloadable_url:
                downloadable_urls.append(downloadable_url)
    
    # Save the results
    save_json_file(sample_input, "sample_input.json")
    save_json_file(downloadable_urls, output_file)
    
    logger.info(f"Found {len(downloadable_urls)} downloadable URLs out of {len(sample_input)} input URLs")
    logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
