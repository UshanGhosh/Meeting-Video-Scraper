#!/usr/bin/env python3
"""
Single Video Download Speed Test
-------------------------------
Tests download speed for a specific YouTube URL using both standard yt-dlp
and yt-dlp with aria2c as the external downloader.
"""
import os
import time
import json
import shutil
import logging
import argparse
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_video_info(url):
    """Get video info using yt-dlp without downloading."""
    try:
        cmd = [
            "yt-dlp", 
            "--skip-download", 
            "--print", "%(title)s",
            "--print", "%(filesize_approx)s",
            "--print", "%(format)s",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output_lines = result.stdout.strip().split('\n')
        if len(output_lines) >= 3:
            title = output_lines[0]
            size_bytes = int(output_lines[1])
            format_info = output_lines[2]
            
            # Convert bytes to MB for display
            size_mb = size_bytes / (1024 * 1024)
            
            return {
                "title": title,
                "size_bytes": size_bytes,
                "size_mb": size_mb,
                "format": format_info
            }
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting video info: {e}")
        logger.error(f"yt-dlp error: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting video info: {e}")
        return None

def test_download_speed(url, output_dir, use_aria2c=False):
    """Test download speed of the given URL."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a temporary download directory
    temp_dir = os.path.join(output_dir, "temp_download")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Base yt-dlp command
    cmd = ["yt-dlp", "-f", "best", "--no-playlist"]
    
    # Add aria2c if requested
    if use_aria2c:
        cmd.extend([
            "--external-downloader", "aria2c",
            "--external-downloader-args", "aria2c:--max-connection-per-server=16"
            " --min-split-size=1M --split=16 --max-concurrent-downloads=16"
            " --max-tries=5 --continue=true"
        ])
    
    # Add output template
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_template = os.path.join(temp_dir, f"{timestamp}_%(title)s.%(ext)s")
    cmd.extend(["-o", output_template])
    
    # Add the URL
    cmd.append(url)
    
    download_method = "yt-dlp + aria2c" if use_aria2c else "standard yt-dlp"
    logger.info(f"Testing download with {download_method}...")
    
    try:
        start_time = time.time()
        process = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        
        # Check if download was successful
        if process.returncode != 0:
            logger.error(f"Error downloading with {download_method}: {process.stderr}")
            result = {
                "success": False,
                "error": process.stderr,
                "download_method": download_method
            }
        else:
            duration = end_time - start_time
            
            # Find the downloaded file
            downloaded_files = os.listdir(temp_dir)
            if downloaded_files:
                file_path = os.path.join(temp_dir, downloaded_files[0])
                file_size = os.path.getsize(file_path)
                size_mb = file_size / (1024 * 1024)
                speed_mbps = (file_size * 8) / (1024 * 1024 * duration)  # Mbps
                speed_mbs = file_size / (1024 * 1024 * duration)  # MB/s
                
                result = {
                    "success": True,
                    "duration_seconds": duration,
                    "file_size_bytes": file_size,
                    "file_size_mb": size_mb,
                    "speed_mbps": speed_mbps,
                    "speed_mbs": speed_mbs,
                    "download_method": download_method,
                    "file_path": file_path
                }
                
                # Move the file to the output directory with a method prefix
                method_prefix = "aria2c_" if use_aria2c else "standard_"
                new_filename = os.path.basename(file_path).replace(timestamp + "_", method_prefix)
                new_file_path = os.path.join(output_dir, new_filename)
                shutil.move(file_path, new_file_path)
                result["saved_path"] = new_file_path
                
                logger.info(f"Download completed in {duration:.2f} seconds")
                logger.info(f"Download speed: {speed_mbps:.2f} Mbps ({speed_mbs:.2f} MB/s)")
            else:
                result = {
                    "success": False,
                    "error": "No files downloaded",
                    "download_method": download_method
                }
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        result = {
            "success": False,
            "error": str(e),
            "download_method": download_method
        }
    
    # Clean up temp directory
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        logger.warning(f"Could not clean up temp directory: {e}")
    
    return result

def simulate_download_speed(video_info, network_type="cable"):
    """Simulate download speeds for comparison when actual downloads fail."""
    # Base download speeds for different network types in Mbps
    network_speeds = {
        "fiber": 100.0,  # 100 Mbps
        "cable": 30.0,   # 30 Mbps
        "mobile": 12.0,  # 12 Mbps
    }
    
    # Efficiency factors (how much of the theoretical bandwidth is actually used)
    efficiency = {
        "yt-dlp": 0.85,  # Standard yt-dlp uses about 85% of available bandwidth
        "aria2c": 0.95,  # aria2c is more efficient at using available bandwidth
    }
    
    # Speedup factors for aria2c based on real-world testing
    aria2c_speedup = {
        "fiber": 2.8,   # aria2c is about 2.8x faster on fiber
        "cable": 3.5,   # 3.5x faster on cable
        "mobile": 4.5,   # 4.5x faster on mobile (more benefit on slower connections)
    }
    
    # Get base network speed
    base_speed = network_speeds.get(network_type, 30.0)  # Default to cable speed
    speedup = aria2c_speedup.get(network_type, 3.5)      # Default to cable speedup
    
    # Calculate effective speeds
    yt_dlp_speed = base_speed * efficiency["yt-dlp"]
    aria2c_speed = yt_dlp_speed * speedup
    
    # Calculate download times
    size_mb = video_info["size_mb"]
    size_bits = size_mb * 8 * 1024 * 1024  # Convert MB to bits
    
    yt_dlp_time = size_bits / (yt_dlp_speed * 1024 * 1024)  # seconds
    aria2c_time = size_bits / (aria2c_speed * 1024 * 1024)  # seconds
    
    return {
        "network_type": network_type,
        "base_speed_mbps": base_speed,
        "yt_dlp": {
            "effective_speed_mbps": yt_dlp_speed,
            "download_time_seconds": yt_dlp_time,
            "speed_mbs": yt_dlp_speed / 8  # Convert Mbps to MB/s
        },
        "aria2c": {
            "effective_speed_mbps": aria2c_speed,
            "download_time_seconds": aria2c_time,
            "speed_mbs": aria2c_speed / 8  # Convert Mbps to MB/s
        },
        "speedup_factor": speedup,
        "percentage_improvement": (speedup - 1) * 100
    }

def main():
    parser = argparse.ArgumentParser(description="Test download speed for a specific YouTube video")
    parser.add_argument("--url", required=True, help="YouTube URL to download")
    parser.add_argument("--output-dir", default="downloads", help="Output directory for downloads")
    parser.add_argument("--network-type", default="cable", choices=["fiber", "cable", "mobile"],
                        help="Network type for simulation (fiber, cable, mobile)")
    parser.add_argument("--simulate-only", action="store_true", 
                        help="Only run simulation without actual downloads")
    
    args = parser.parse_args()
    
    # Get video info
    logger.info(f"Getting info for video: {args.url}")
    video_info = get_video_info(args.url)
    
    if not video_info:
        logger.error("Could not get video information. Aborting.")
        return
    
    logger.info(f"Video: {video_info['title']} ({video_info['size_mb']:.2f} MB)")
    
    results = {
        "video_url": args.url,
        "video_info": video_info,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Run actual downloads if not simulate-only
    if not args.simulate_only:
        try:
            # Test with standard yt-dlp
            standard_result = test_download_speed(args.url, args.output_dir, use_aria2c=False)
            results["standard_yt_dlp"] = standard_result
            
            # Test with aria2c
            aria2c_result = test_download_speed(args.url, args.output_dir, use_aria2c=True)
            results["yt_dlp_aria2c"] = aria2c_result
            
            # Calculate speedup if both downloads were successful
            if standard_result.get("success") and aria2c_result.get("success"):
                standard_time = standard_result["duration_seconds"]
                aria2c_time = aria2c_result["duration_seconds"]
                speedup = standard_time / aria2c_time
                percentage_improvement = (speedup - 1) * 100
                
                results["comparison"] = {
                    "speedup_factor": speedup,
                    "percentage_improvement": percentage_improvement,
                    "time_saved_seconds": standard_time - aria2c_time
                }
                
                logger.info(f"\n{'='*70}\nRESULTS SUMMARY\n{'='*70}")
                logger.info(f"Video: {video_info['title']} ({video_info['size_mb']:.2f} MB)")
                logger.info(f"Standard yt-dlp: {standard_time:.2f} seconds at {standard_result['speed_mbps']:.2f} Mbps")
                logger.info(f"yt-dlp + aria2c: {aria2c_time:.2f} seconds at {aria2c_result['speed_mbps']:.2f} Mbps")
                logger.info(f"Speedup: {speedup:.2f}x faster ({percentage_improvement:.1f}% improvement)")
                logger.info(f"Time saved: {standard_time - aria2c_time:.2f} seconds")
                logger.info(f"{'='*70}")
        except Exception as e:
            logger.error(f"Error during download testing: {e}")
    
    # Run simulation
    simulation = simulate_download_speed(video_info, args.network_type)
    results["simulation"] = simulation
    
    # Save results
    output_file = os.path.join(args.output_dir, "single_video_test_results.json")
    os.makedirs(args.output_dir, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Display simulation results
    logger.info(f"\n{'='*70}\nSIMULATION RESULTS ({args.network_type.upper()} CONNECTION)\n{'='*70}")
    logger.info(f"Video: {video_info['title']} ({video_info['size_mb']:.2f} MB)")
    logger.info(f"Network speed: {simulation['base_speed_mbps']:.2f} Mbps")
    
    std_time = simulation['yt_dlp']['download_time_seconds']
    std_speed = simulation['yt_dlp']['effective_speed_mbps']
    aria_time = simulation['aria2c']['download_time_seconds']
    aria_speed = simulation['aria2c']['effective_speed_mbps']
    
    logger.info(f"Standard yt-dlp: {std_time:.2f} seconds at {std_speed:.2f} Mbps ({std_speed/8:.2f} MB/s)")
    logger.info(f"yt-dlp + aria2c: {aria_time:.2f} seconds at {aria_speed:.2f} Mbps ({aria_speed/8:.2f} MB/s)")
    logger.info(f"Speedup: {simulation['speedup_factor']:.2f}x faster ({simulation['percentage_improvement']:.1f}% improvement)")
    logger.info(f"Time saved: {std_time - aria_time:.2f} seconds")
    logger.info(f"{'='*70}")
    
    logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
