#!/usr/bin/env python3
"""
Download Speed Comparison: yt-dlp vs yt-dlp with aria2c

This script:
1. Loads downloadable URLs from video_extractor/downloadable_videos.json
2. Downloads each video twice:
   - First with standard yt-dlp
   - Then with yt-dlp + aria2c
3. Compares and reports the download speeds
"""

import os
import sys
import json
import time
import shutil
import logging
import math
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("speed_comparison.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
YT_DLP_DIR = "yt_dlp_downloads"
ARIA2C_DIR = "aria2c_downloads"
DOWNLOAD_BASE_DIR = "comparison_downloads"
JSON_PATH = "../video_extractor/downloadable_videos.json"

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        from yt_dlp import YoutubeDL
        logger.info("✅ yt-dlp is installed")
    except ImportError:
        logger.error("❌ yt-dlp is not installed. Please install it with: pip install yt-dlp")
        sys.exit(1)
    
    # Check for aria2c
    try:
        result = subprocess.run(['aria2c', '--version'], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            logger.info(f"✅ aria2c is installed: {version}")
        else:
            logger.error("❌ aria2c command failed. Please ensure it's installed and in your PATH.")
            logger.error("Install aria2c: https://aria2.github.io/")
            sys.exit(1)
    except FileNotFoundError:
        logger.error("❌ aria2c is not installed or not in PATH. Please install it from https://aria2.github.io/")
        sys.exit(1)

def create_download_directories():
    """Create download directories for both methods."""
    base_dir = Path(DOWNLOAD_BASE_DIR)
    yt_dlp_dir = base_dir / YT_DLP_DIR
    aria2c_dir = base_dir / ARIA2C_DIR
    
    # Clear existing directories
    if base_dir.exists():
        shutil.rmtree(base_dir)
    
    # Create fresh directories
    yt_dlp_dir.mkdir(parents=True, exist_ok=True)
    aria2c_dir.mkdir(parents=True, exist_ok=True)
    
    return str(yt_dlp_dir), str(aria2c_dir)

def load_urls():
    """Load URLs from the downloadable_videos.json file."""
    try:
        with open(JSON_PATH, 'r') as f:
            urls = json.load(f)
        
        if isinstance(urls, list):
            logger.info(f"Loaded {len(urls)} URLs from {JSON_PATH}")
            return urls
        else:
            logger.error(f"Unexpected format in {JSON_PATH}. Expected a list of URLs.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading URLs from {JSON_PATH}: {str(e)}")
        sys.exit(1)

def download_with_ytdlp(url, output_dir):
    """
    Download a video using standard yt-dlp without aria2c.
    
    Returns:
        tuple: (success, download_time, file_size, file_path)
    """
    try:
        from yt_dlp import YoutubeDL
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'restrictfilenames': True,
            'noplaylist': True,
            'no_warnings': False,
            'quiet': True,
        }
        
        logger.info(f"Starting standard yt-dlp download for: {url}")
        
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
        
        logger.info(f"Standard yt-dlp download completed in {download_time:.2f} seconds")
        return True, download_time, file_size, file_path
    
    except Exception as e:
        logger.error(f"Error downloading with yt-dlp: {str(e)}")
        return False, 0, 0, None

def download_with_aria2c(url, output_dir):
    """
    Download a video using yt-dlp with aria2c as the external downloader.
    
    Returns:
        tuple: (success, download_time, file_size, file_path)
    """
    try:
        from yt_dlp import YoutubeDL
        
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
            'format': 'best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'external_downloader': 'aria2c',
            'external_downloader_args': {
                'aria2c': aria2c_params
            },
            'restrictfilenames': True,
            'noplaylist': True,
            'no_warnings': False,
            'quiet': True,
        }
        
        logger.info(f"Starting yt-dlp + aria2c download for: {url}")
        
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
        
        logger.info(f"yt-dlp + aria2c download completed in {download_time:.2f} seconds")
        return True, download_time, file_size, file_path
    
    except Exception as e:
        logger.error(f"Error downloading with aria2c: {str(e)}")
        return False, 0, 0, None

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

def compare_downloads(urls):
    """
    Download each URL with both methods and compare the speeds.
    
    Args:
        urls: List of URLs to download
        
    Returns:
        dict: Comparison results
    """
    # Create download directories
    yt_dlp_dir, aria2c_dir = create_download_directories()
    
    results = []
    
    for i, url in enumerate(urls, 1):
        logger.info(f"Testing URL {i}/{len(urls)}: {url}")
        print(f"\n[{i}/{len(urls)}] Testing URL: {url}")
        
        result = {
            "url": url,
            "yt_dlp": {},
            "aria2c": {}
        }
        
        # Download with standard yt-dlp
        print("⏳ Downloading with standard yt-dlp...")
        yt_dlp_success, yt_dlp_time, yt_dlp_size, yt_dlp_file = download_with_ytdlp(url, yt_dlp_dir)
        
        if yt_dlp_success:
            result["yt_dlp"] = {
                "success": True,
                "download_time": yt_dlp_time,
                "file_size": yt_dlp_size,
                "file_path": yt_dlp_file,
                "download_speed": format_speed(yt_dlp_size, yt_dlp_time)
            }
            print(f"✅ yt-dlp download completed in {yt_dlp_time:.2f} seconds")
            print(f"   File size: {format_size(yt_dlp_size)}")
            print(f"   Average speed: {format_speed(yt_dlp_size, yt_dlp_time)}")
        else:
            result["yt_dlp"] = {
                "success": False
            }
            print("❌ yt-dlp download failed")
        
        # Short delay between downloads
        time.sleep(2)
        
        # Download with yt-dlp + aria2c
        print("\n⏳ Downloading with yt-dlp + aria2c...")
        aria2c_success, aria2c_time, aria2c_size, aria2c_file = download_with_aria2c(url, aria2c_dir)
        
        if aria2c_success:
            result["aria2c"] = {
                "success": True,
                "download_time": aria2c_time,
                "file_size": aria2c_size,
                "file_path": aria2c_file,
                "download_speed": format_speed(aria2c_size, aria2c_time)
            }
            print(f"✅ aria2c download completed in {aria2c_time:.2f} seconds")
            print(f"   File size: {format_size(aria2c_size)}")
            print(f"   Average speed: {format_speed(aria2c_size, aria2c_time)}")
        else:
            result["aria2c"] = {
                "success": False
            }
            print("❌ aria2c download failed")
        
        # Calculate speed improvement if both methods succeeded
        if yt_dlp_success and aria2c_success:
            if yt_dlp_time > 0:
                speedup = yt_dlp_time / aria2c_time
                result["speedup"] = speedup
                result["percentage_faster"] = (speedup - 1) * 100
                print(f"\n🚀 RESULT: aria2c is {speedup:.2f}x faster ({result['percentage_faster']:.2f}% improvement)")
                
                # Add normalized comparison (accounting for any file size differences)
                if yt_dlp_size > 0 and aria2c_size > 0:
                    yt_dlp_bytes_per_sec = yt_dlp_size / yt_dlp_time
                    aria2c_bytes_per_sec = aria2c_size / aria2c_time
                    speed_ratio = aria2c_bytes_per_sec / yt_dlp_bytes_per_sec
                    result["speed_ratio"] = speed_ratio
                    print(f"   Speed ratio (accounting for file size): {speed_ratio:.2f}x")
        
        results.append(result)
    
    return results

def save_results(results):
    """Save comparison results to a JSON file."""
    try:
        output_file = "download_speed_comparison.json"
        
        # Calculate overall statistics
        successful_comparisons = [r for r in results if r.get("speedup")]
        
        if successful_comparisons:
            avg_speedup = sum(r["speedup"] for r in successful_comparisons) / len(successful_comparisons)
            avg_percentage = sum(r["percentage_faster"] for r in successful_comparisons) / len(successful_comparisons)
            
            if all("speed_ratio" in r for r in successful_comparisons):
                avg_speed_ratio = sum(r["speed_ratio"] for r in successful_comparisons) / len(successful_comparisons)
            else:
                avg_speed_ratio = None
        else:
            avg_speedup = 0
            avg_percentage = 0
            avg_speed_ratio = None
        
        output_data = {
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "urls_tested": len(results),
            "successful_comparisons": len(successful_comparisons),
            "average_speedup": avg_speedup,
            "average_percentage_faster": avg_percentage,
            "average_speed_ratio": avg_speed_ratio,
            "detailed_results": results
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        return output_data
    
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        return None

def print_summary(stats):
    """Print a summary of the comparison results."""
    if not stats:
        return
    
    print("\n" + "="*70)
    print("📊 DOWNLOAD SPEED COMPARISON SUMMARY 📊".center(70))
    print("="*70)
    print(f"🔹 URLs tested: {stats['urls_tested']}")
    print(f"🔹 Successful comparisons: {stats['successful_comparisons']}")
    
    if stats['successful_comparisons'] > 0:
        print(f"🔹 Average speedup with aria2c: {stats['average_speedup']:.2f}x")
        print(f"🔹 Average percentage faster: {stats['average_percentage_faster']:.2f}%")
        
        if stats['average_speed_ratio']:
            print(f"🔹 Average speed ratio (accounting for file size): {stats['average_speed_ratio']:.2f}x")
    
    print("="*70)
    
    if stats['detailed_results']:
        print("\n📑 DETAILED RESULTS:")
        
        for i, result in enumerate(stats['detailed_results'], 1):
            print(f"\n🔸 URL {i}: {result['url']}")
            
            if result['yt_dlp'].get('success') and result['aria2c'].get('success'):
                yt_dlp_time = result['yt_dlp']['download_time']
                aria2c_time = result['aria2c']['download_time']
                yt_dlp_speed = result['yt_dlp'].get('download_speed', 'N/A')
                aria2c_speed = result['aria2c'].get('download_speed', 'N/A')
                
                print(f"  • yt-dlp: {yt_dlp_time:.2f} seconds (Speed: {yt_dlp_speed})")
                print(f"  • aria2c: {aria2c_time:.2f} seconds (Speed: {aria2c_speed})")
                
                if "speedup" in result:
                    print(f"  • Improvement: {result['speedup']:.2f}x faster ({result['percentage_faster']:.2f}%)")
            else:
                if not result['yt_dlp'].get('success'):
                    print("  • yt-dlp download failed")
                if not result['aria2c'].get('success'):
                    print("  • aria2c download failed")
    
    print("\n" + "="*70)
    print(f"📄 Complete results saved to download_speed_comparison.json")
    print("="*70)

def main():
    """Main function to run the comparison."""
    print("\n🔍 STARTING DOWNLOAD SPEED COMPARISON: yt-dlp vs yt-dlp with aria2c\n")
    
    # Check if dependencies are installed
    check_dependencies()
    
    # Load URLs from JSON file
    urls = load_urls()
    
    if not urls:
        logger.error("No URLs to download. Please check the JSON file.")
        sys.exit(1)
    
    # Compare download speeds
    results = compare_downloads(urls)
    
    # Save and print results
    stats = save_results(results)
    print_summary(stats)
    
    print("\n✨ Speed comparison completed! ✨\n")

if __name__ == "__main__":
    main()
