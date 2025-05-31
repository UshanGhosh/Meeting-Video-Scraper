#!/usr/bin/env python3
"""
Fast Video Downloader with yt-dlp and aria2c

This script demonstrates how to use yt-dlp programmatically via Python
with aria2c as an external downloader for faster, multi-threaded downloads.

Features:
- Configures aria2c with multiple connections
- Uses split downloading for large files
- Implements optimized retry policies
- Provides download progress tracking
- Allows batch downloading from a JSON file
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fast_downloader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        from yt_dlp import YoutubeDL
        logger.info("yt-dlp is installed")
    except ImportError:
        logger.error("yt-dlp is not installed. Please install it with: pip install yt-dlp")
        sys.exit(1)
    
    # Check for aria2c
    import subprocess
    try:
        result = subprocess.run(['aria2c', '--version'], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            logger.info(f"aria2c is installed: {version}")
        else:
            logger.error("aria2c command failed. Please ensure it's installed and in your PATH.")
            logger.error("Install aria2c: https://aria2.github.io/")
            sys.exit(1)
    except FileNotFoundError:
        logger.error("aria2c is not installed or not in PATH. Please install it from https://aria2.github.io/")
        sys.exit(1)

def create_download_directory(directory):
    """Create download directory if it doesn't exist."""
    download_dir = Path(directory)
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir

def download_video(url, output_dir, filename=None, quality='best'):
    """
    Download a video using yt-dlp with aria2c as the external downloader.
    
    Args:
        url: URL of the video to download
        output_dir: Directory to save the downloaded video
        filename: Optional filename template (without extension)
        quality: Video quality to download
        
    Returns:
        dict: Information about the downloaded video
    """
    try:
        from yt_dlp import YoutubeDL
        
        # Create a custom progress hook
        def progress_hook(d):
            if d['status'] == 'downloading':
                if '_percent_str' in d:
                    percent = d['_percent_str']
                    speed = d.get('_speed_str', 'N/A')
                    eta = d.get('_eta_str', 'N/A')
                    logger.info(f"Downloading: {percent} complete, Speed: {speed}, ETA: {eta}")
            elif d['status'] == 'finished':
                logger.info(f"Download finished. Converting...")
            elif d['status'] == 'error':
                logger.error(f"Error downloading: {d.get('error')}")
        
        # Configure aria2c parameters for optimal performance
        aria2c_params = [
            '--max-connection-per-server=16',  # Maximum connections per server
            '--min-split-size=1M',             # Minimum split size
            '--split=16',                      # Split file into 16 parts
            '--max-concurrent-downloads=16',   # Maximum concurrent downloads
            '--max-tries=5',                   # Maximum retry attempts
            '--retry-wait=2',                  # Wait 2 seconds between retries
            '--connect-timeout=10',            # Connection timeout
            '--allow-overwrite=true',          # Allow overwriting existing files
            '--auto-file-renaming=false',      # Disable auto file renaming
            '--continue=true',                 # Resume downloads
            '--console-log-level=warn'         # Reduce console logging
        ]
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': quality,
            'outtmpl': os.path.join(output_dir, f'%(title)s.%(ext)s' if not filename else f'{filename}.%(ext)s'),
            'progress_hooks': [progress_hook],
            'external_downloader': 'aria2c',
            'external_downloader_args': {
                'aria2c': aria2c_params
            },
            'restrictfilenames': True,  # Restrict filenames to ASCII characters
            'noplaylist': True,         # Download single video, not playlist
            'no_warnings': False,       # Show warnings
            'ignoreerrors': False,      # Don't ignore errors
            'verbose': True,            # Verbose output
        }
        
        # Create YoutubeDL instance and download the video
        logger.info(f"Starting download of {url} with aria2c")
        start_time = time.time()
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
        end_time = time.time()
        download_time = end_time - start_time
        
        # Return information about the downloaded video
        if info:
            result = {
                'title': info.get('title', 'Unknown'),
                'url': url,
                'filename': ydl.prepare_filename(info),
                'duration': info.get('duration', 0),
                'download_time': download_time,
                'success': True
            }
            logger.info(f"Successfully downloaded {result['title']} in {download_time:.2f} seconds")
            return result
        else:
            logger.error(f"Failed to download {url}")
            return {'url': url, 'success': False}
            
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return {'url': url, 'success': False, 'error': str(e)}

def batch_download_from_json(json_file, output_dir, quality='best'):
    """
    Download multiple videos from a JSON file.
    
    Args:
        json_file: Path to JSON file containing video URLs
        output_dir: Directory to save downloaded videos
        quality: Video quality to download
        
    Returns:
        list: Results of all downloads
    """
    try:
        # Load JSON file
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Extract URLs from the JSON structure
        urls = []
        if isinstance(data, list):
            # If data is a list of URLs
            urls = data
        elif isinstance(data, dict) and 'downloadable_urls' in data:
            # If data has a 'downloadable_urls' key (like our test results)
            urls = data['downloadable_urls']
        elif isinstance(data, dict) and 'results' in data:
            # If data has a 'results' key with embedded 'downloadable_videos'
            for result in data['results']:
                if 'downloadable_videos' in result:
                    urls.extend(result['downloadable_videos'])
        
        if not urls:
            logger.error(f"No valid URLs found in {json_file}")
            return []
        
        # Download each video
        logger.info(f"Found {len(urls)} URLs to download")
        results = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Downloading video {i}/{len(urls)}: {url}")
            result = download_video(url, output_dir, quality=quality)
            results.append(result)
        
        # Save download results
        results_file = os.path.join(output_dir, 'download_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        success_count = sum(1 for r in results if r.get('success', False))
        logger.info(f"Download complete: {success_count}/{len(urls)} videos successfully downloaded")
        logger.info(f"Results saved to {results_file}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in batch download: {str(e)}")
        return []

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fast Video Downloader using yt-dlp with aria2c")
    
    # Add arguments
    parser.add_argument("--url", help="URL of the video to download")
    parser.add_argument("--json-file", help="Path to JSON file containing video URLs")
    parser.add_argument("--output-dir", default="downloads", help="Directory to save downloaded videos")
    parser.add_argument("--quality", default="best", help="Video quality to download")
    parser.add_argument("--filename", help="Optional filename template (without extension)")
    
    return parser.parse_args()

def main():
    """Main function to run the downloader."""
    args = parse_arguments()
    
    # Check if required dependencies are installed
    check_dependencies()
    
    # Create download directory
    output_dir = create_download_directory(args.output_dir)
    logger.info(f"Download directory: {output_dir}")
    
    # Check if URL or JSON file is provided
    if args.url:
        # Download single video
        download_video(args.url, output_dir, args.filename, args.quality)
    elif args.json_file:
        # Batch download from JSON file
        batch_download_from_json(args.json_file, output_dir, args.quality)
    else:
        logger.error("Please provide either a URL or a JSON file")
        sys.exit(1)

if __name__ == "__main__":
    main()
