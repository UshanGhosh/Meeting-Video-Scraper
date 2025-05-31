#!/usr/bin/env python3
"""
Fast Video Downloader with yt-dlp

This script implements a video downloader that:
1. Uses yt-dlp programmatically via Python
2. Optionally uses aria2c with optimized parameters if available
3. Downloads videos from a JSON list (from video_extractor/downloadable_videos.json)
4. Provides detailed information about download speed and performance

The script will work even if aria2c is not installed, but will use it for faster
downloads if available.
"""

import os
import sys
import json
import time
import logging
import math
import subprocess
from pathlib import Path
import shutil

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

# Constants
DEFAULT_OUTPUT_DIR = "downloads"
DEFAULT_JSON_PATH = "../video_extractor/downloadable_videos.json"

def check_dependencies():
    """
    Check if required dependencies are installed.
    Returns True if aria2c is available, False otherwise.
    """
    try:
        from yt_dlp import YoutubeDL
        logger.info("✅ yt-dlp is installed")
    except ImportError:
        logger.error("❌ yt-dlp is not installed. Please install it with: pip install yt-dlp")
        sys.exit(1)
    
    # Check for aria2c (optional)
    try:
        result = subprocess.run(['aria2c', '--version'], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            logger.info(f"✅ aria2c is installed: {version}")
            return True
        else:
            logger.warning("⚠️ aria2c command failed. Will use standard yt-dlp for downloads.")
            return False
    except FileNotFoundError:
        logger.warning("⚠️ aria2c is not installed. Will use standard yt-dlp for downloads.")
        logger.info("To install aria2c for faster downloads:")
        logger.info("  macOS: brew install aria2")
        logger.info("  Ubuntu/Debian: sudo apt-get install aria2")
        logger.info("  Windows: Download from https://aria2.github.io/")
        return False

def create_download_directory(directory):
    """Create download directory if it doesn't exist."""
    download_dir = Path(directory)
    download_dir.mkdir(parents=True, exist_ok=True)
    return str(download_dir)

def load_urls(json_path):
    """Load URLs from the downloadable_videos.json file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON formats
        urls = []
        if isinstance(data, list):
            # Direct list of URLs (like downloadable_videos.json)
            urls = data
        elif isinstance(data, dict) and "downloadable_urls" in data:
            # Format from test results
            urls = data["downloadable_urls"]
        
        if urls:
            logger.info(f"Loaded {len(urls)} URLs from {json_path}")
            return urls
        else:
            logger.error(f"No URLs found in {json_path}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading URLs from {json_path}: {str(e)}")
        sys.exit(1)

def format_size(size_bytes):
    """Format file size in a human-readable format."""
    if size_bytes == 0:
        return "0B"
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.log(size_bytes, 1024))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def format_speed(size_bytes, seconds):
    """Calculate and format download speed."""
    if seconds == 0:
        return "N/A"
    bytes_per_second = size_bytes / seconds
    return format_size(bytes_per_second) + "/s"

def download_video(url, output_dir, use_aria2c=False, filename=None):
    """
    Download a video using yt-dlp, optionally with aria2c.
    
    Args:
        url: URL of the video to download
        output_dir: Directory to save the downloaded video
        use_aria2c: Whether to use aria2c as external downloader
        filename: Optional filename template (without extension)
        
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
                    print(f"⏳ Downloading: {percent} complete, Speed: {speed}, ETA: {eta}", end='\r')
            elif d['status'] == 'finished':
                print("\n✅ Download finished. Processing...")
            elif d['status'] == 'error':
                print(f"\n❌ Error downloading: {d.get('error')}")
        
        # Base yt-dlp options
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(output_dir, f'%(title)s.%(ext)s' if not filename else f'{filename}.%(ext)s'),
            'progress_hooks': [progress_hook],
            'restrictfilenames': True,  # Restrict filenames to ASCII characters
            'noplaylist': True,         # Download single video, not playlist
            'no_warnings': False,       # Show warnings
        }
        
        # If aria2c is available and requested, configure it with optimized parameters
        if use_aria2c:
            aria2c_params = [
                '--max-connection-per-server=16',  # Maximum connections per server
                '--min-split-size=1M',             # Minimum split size
                '--split=16',                      # Split file into 16 parts
                '--max-concurrent-downloads=16',   # Maximum concurrent downloads
                '--max-tries=5',                   # Maximum retry attempts
                '--retry-wait=2',                  # Wait 2 seconds between retries
                '--connect-timeout=10',            # Connection timeout
                '--allow-overwrite=true',          # Allow overwriting existing files
                '--continue=true',                 # Resume downloads
                '--console-log-level=warn'         # Reduce console logging
            ]
            
            ydl_opts['external_downloader'] = 'aria2c'
            ydl_opts['external_downloader_args'] = {
                'aria2c': aria2c_params
            }
            logger.info(f"Starting download with yt-dlp + aria2c: {url}")
            print(f"🚀 Starting download with yt-dlp + aria2c acceleration: {url}")
        else:
            logger.info(f"Starting download with standard yt-dlp: {url}")
            print(f"🔄 Starting download with standard yt-dlp: {url}")
        
        # Start timer
        start_time = time.time()
        
        # Download the video
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        
        # End timer
        end_time = time.time()
        download_time = end_time - start_time
        
        # Get file size
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # Return information about the downloaded video
        result = {
            'title': info.get('title', 'Unknown'),
            'url': url,
            'filename': os.path.basename(file_path),
            'file_path': file_path,
            'file_size': file_size,
            'human_size': format_size(file_size),
            'download_time': download_time,
            'download_speed': format_speed(file_size, download_time),
            'used_aria2c': use_aria2c,
            'success': True
        }
        
        logger.info(f"Successfully downloaded {result['title']} in {download_time:.2f} seconds")
        logger.info(f"File size: {result['human_size']}, Speed: {result['download_speed']}")
        
        print(f"✅ Download complete: {result['title']}")
        print(f"   Time: {download_time:.2f} seconds")
        print(f"   Size: {result['human_size']}")
        print(f"   Speed: {result['download_speed']}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        print(f"❌ Download failed: {url}")
        print(f"   Error: {str(e)}")
        return {
            'url': url,
            'success': False,
            'error': str(e),
            'used_aria2c': use_aria2c
        }

def batch_download(urls, output_dir, use_aria2c=False):
    """
    Download multiple videos from a list of URLs.
    
    Args:
        urls: List of URLs to download
        output_dir: Directory to save downloaded videos
        use_aria2c: Whether to use aria2c as external downloader
        
    Returns:
        list: Results of all downloads
    """
    results = []
    successful = 0
    failed = 0
    total_time = 0
    total_size = 0
    
    print(f"\n📋 Starting batch download of {len(urls)} videos")
    print(f"📂 Output directory: {output_dir}")
    print(f"🛠️ Using {'yt-dlp + aria2c' if use_aria2c else 'standard yt-dlp'}\n")
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing URL: {url}")
        
        # Download the video
        result = download_video(url, output_dir, use_aria2c)
        results.append(result)
        
        # Update statistics
        if result.get('success', False):
            successful += 1
            total_time += result.get('download_time', 0)
            total_size += result.get('file_size', 0)
        else:
            failed += 1
    
    # Calculate overall statistics
    avg_time = total_time / successful if successful > 0 else 0
    avg_speed = format_speed(total_size, total_time) if total_time > 0 else "N/A"
    
    # Print summary
    print("\n" + "="*70)
    print("📊 DOWNLOAD SUMMARY 📊".center(70))
    print("="*70)
    print(f"🔸 Total URLs: {len(urls)}")
    print(f"🔸 Successful: {successful}")
    print(f"🔸 Failed: {failed}")
    
    if successful > 0:
        print(f"🔸 Total download time: {total_time:.2f} seconds")
        print(f"🔸 Total data downloaded: {format_size(total_size)}")
        print(f"🔸 Average download time: {avg_time:.2f} seconds per file")
        print(f"🔸 Average download speed: {avg_speed}")
    
    print("="*70)
    
    # Save results to JSON
    results_file = os.path.join(output_dir, "download_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'urls_total': len(urls),
            'successful': successful,
            'failed': failed,
            'total_time': total_time,
            'total_size': total_size,
            'average_time': avg_time,
            'used_aria2c': use_aria2c,
            'detailed_results': results
        }, f, indent=2)
    
    logger.info(f"Results saved to {results_file}")
    print(f"\n📄 Detailed results saved to {results_file}")
    
    return results

def parse_arguments():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="Fast Video Downloader using yt-dlp with optional aria2c acceleration")
    
    parser.add_argument("--json", default=DEFAULT_JSON_PATH,
                       help=f"Path to JSON file with URLs (default: {DEFAULT_JSON_PATH})")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                       help=f"Directory to save downloaded videos (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--url", help="Single URL to download (instead of using a JSON file)")
    parser.add_argument("--no-aria2c", action="store_true",
                       help="Force using standard yt-dlp even if aria2c is available")
    
    return parser.parse_args()

def main():
    """Main function to run the downloader."""
    print("\n🚀 FAST VIDEO DOWNLOADER 🚀\n")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Check if yt-dlp is installed and if aria2c is available
    aria2c_available = check_dependencies()
    
    # Determine whether to use aria2c
    use_aria2c = aria2c_available and not args.no_aria2c
    
    # Create download directory
    output_dir = create_download_directory(args.output_dir)
    
    if args.url:
        # Download a single URL
        download_video(args.url, output_dir, use_aria2c)
    else:
        # Load URLs from JSON file
        urls = load_urls(args.json)
        
        if not urls:
            logger.error("No URLs to download")
            sys.exit(1)
        
        # Download all URLs
        batch_download(urls, output_dir, use_aria2c)
    
    print("\n✨ Download process completed! ✨\n")

if __name__ == "__main__":
    main()
