#!/usr/bin/env python3
"""
yt-dlp URL Tester

This script tests if specific URLs are downloadable using yt-dlp and outputs the results to a JSON file.
"""

import json
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("yt_dlp_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# List of URLs to test
TEST_URLS = [
    "https://dallastx.new.swagit.com/videos/320946/download",
    "https://www.zoomgov.com/rec/share/vCZnQM5bgMzY7_n4lbQXYnVqsvPj49Ce-R0hMjMFPyG4FUC1HbSyQAZ9uPpRKDvV._6ZMrf7BXZzx6_RK?startTime=1709655569000",
    "https://snohomish.legistar.com/Video.aspx?Mode=Granicus&ID1=9188&Mode2=Video",
    "https://multnomah.granicus.com/MediaPlayer.php?view_id=3&clip_id=3097",
    "https://traviscotx.portal.civicclerk.com/event/2583/media",
    "https://legistar.council.nyc.gov/Video.aspx?Mode=Auto&URL=aHR0cHM6Ly9jb3VuY2lsbnljLnZpZWJpdC5jb20vdm9kLz9zPXRydWUmdj1OWUNDLVBWLTI1MC0xNF8yNDA2MDQtMTAxMzU0Lm1wNA%3d%3d&Mode2=Video",
    "https://video.ibm.com/recorded/134312408",
    "https://cityofalhambraorg-my.sharepoint.com/:v:/g/personal/lmyles_alhambraca_gov/ETs6K1euPsBClaWtczJXl-gB47R9yoz9o9FJYZuEY0KOjA?e=7B41Fy",
    "https://audiomack.com/pemberton-twp-planningzoning-board-meetings/song/678668c3069f2"
]

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
            return url, False, f"Import error: {ie}"
        except Exception as e:
            return url, False, str(e)
    except Exception as e:
        logger.error(f"Error checking URL with yt-dlp: {url}, {str(e)}")
        return url, False, str(e)

def test_urls_parallel():
    """Test URLs in parallel using ThreadPoolExecutor."""
    results = []
    max_workers = min(4, len(TEST_URLS))  # Limit concurrent requests
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(is_downloadable_with_ytdlp, url): url for url in TEST_URLS}
        
        for future in as_completed(future_to_url):
            results.append(future.result())
    
    return results

def test_urls_sequential():
    """Test each URL sequentially and collect results."""
    results = []
    
    for url in TEST_URLS:
        result = is_downloadable_with_ytdlp(url)
        results.append(result)
    
    return results

def format_results(results):
    """Format the test results into a structured dictionary."""
    formatted_results = {
        "downloadable_urls": [],
        "not_downloadable_urls": [],
        "results_details": []
    }
    
    for url, is_downloadable, error in results:
        result_detail = {
            "url": url,
            "is_downloadable": is_downloadable
        }
        
        if error:
            result_detail["error"] = error
            
        formatted_results["results_details"].append(result_detail)
        
        if is_downloadable:
            formatted_results["downloadable_urls"].append(url)
        else:
            formatted_results["not_downloadable_urls"].append(url)
    
    return formatted_results

def save_json_file(data, file_path):
    """Save JSON data to file."""
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)
        logger.info(f"Successfully saved data to {file_path}")
    except Exception as e:
        logger.error(f"Error saving JSON file {file_path}: {e}")

def main():
    """Main function to test URLs and save results."""
    output_file = "yt_dlp_test_results.json"
    
    logger.info(f"Starting yt-dlp URL testing process for {len(TEST_URLS)} URLs")
    
    # Test all URLs (uncomment the preferred method)
    # For sequential processing (more reliable but slower):
    results = test_urls_sequential()
    # For parallel processing (faster but may hit rate limits):
    # results = test_urls_parallel()
    
    # Format and save results
    formatted_results = format_results(results)
    save_json_file(formatted_results, output_file)
    
    # Print summary
    downloadable_count = len(formatted_results["downloadable_urls"])
    total_count = len(TEST_URLS)
    
    logger.info(f"Testing complete: {downloadable_count} out of {total_count} URLs are downloadable")
    logger.info(f"Results saved to {output_file}")
    
    # Print downloadable URLs
    if downloadable_count > 0:
        logger.info("Downloadable URLs:")
        for url in formatted_results["downloadable_urls"]:
            logger.info(f"  - {url}")

if __name__ == "__main__":
    main()
