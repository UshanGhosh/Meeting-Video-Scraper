#!/usr/bin/env python3
"""
Batch Download Example

This script demonstrates how to use the Fast Video Downloader
to batch download videos from the Video Extractor's results.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add parent directory to path so we can import fast_video_downloader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fast_downloader.fast_video_downloader import download_video, check_dependencies, create_download_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_download.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_urls_from_json(json_file):
    """
    Load URLs from the Video Extractor's JSON output.
    Handles different JSON formats from our different tools.
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        urls = []
        
        # Handle different JSON formats
        if isinstance(data, list):
            # Simple list of URLs (like downloadable_videos.json)
            urls = data
            logger.info(f"Loaded {len(urls)} URLs from list format")
            
        elif isinstance(data, dict):
            # Check for different key formats
            if "downloadable_urls" in data:
                # Format from test_yt_dlp_urls.py
                urls = data["downloadable_urls"]
                logger.info(f"Loaded {len(urls)} URLs from 'downloadable_urls' key")
                
            elif "results" in data:
                # Format from embedded_video_test_results.json
                for result in data["results"]:
                    if "downloadable_videos" in result:
                        urls.extend(result["downloadable_videos"])
                logger.info(f"Loaded {len(urls)} URLs from 'results.downloadable_videos' structure")
        
        return urls
    
    except Exception as e:
        logger.error(f"Error loading URLs from {json_file}: {str(e)}")
        return []

def main():
    """Main function to batch download videos."""
    parser = argparse.ArgumentParser(description="Batch download videos from JSON results")
    
    parser.add_argument("--json-file", required=True, 
                        help="Path to JSON file with downloadable URLs")
    parser.add_argument("--output-dir", default="downloads",
                        help="Directory to save downloaded videos")
    
    args = parser.parse_args()
    
    # Check if aria2c and yt-dlp are installed
    check_dependencies()
    
    # Create download directory
    output_dir = create_download_directory(args.output_dir)
    logger.info(f"Download directory: {output_dir}")
    
    # Load URLs from JSON file
    urls = load_urls_from_json(args.json_file)
    
    if not urls:
        logger.error("No URLs found to download. Please check your JSON file.")
        sys.exit(1)
    
    logger.info(f"Found {len(urls)} URLs to download")
    
    # Download each video
    successful = 0
    failed = 0
    
    for i, url in enumerate(urls, 1):
        logger.info(f"Downloading video {i}/{len(urls)}: {url}")
        result = download_video(url, output_dir)
        
        if result.get('success', False):
            successful += 1
        else:
            failed += 1
    
    # Print summary
    logger.info(f"Download complete: {successful} successful, {failed} failed")
    logger.info(f"Videos saved to {output_dir}")

if __name__ == "__main__":
    main()
