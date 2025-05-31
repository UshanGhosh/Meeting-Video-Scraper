#!/usr/bin/env python3
"""
Simulate Download Speed Comparison: yt-dlp vs yt-dlp with aria2c

This script simulates the download speeds of standard yt-dlp versus
yt-dlp with aria2c to demonstrate the expected performance improvements
without requiring actual downloads.
"""

import json
import time
import random
import os
from datetime import datetime

# Sample video information with realistic sizes
SAMPLE_VIDEOS = [
    {
        "title": "City Council Meeting (HD)",
        "url": "https://example.com/videos/council_meeting_hd.mp4",
        "size_mb": 850,  # 850 MB file
        "quality": "1080p"
    },
    {
        "title": "Public Hearing on Zoning (SD)",
        "url": "https://example.com/videos/public_hearing.mp4",
        "size_mb": 320,  # 320 MB file
        "quality": "720p"
    },
    {
        "title": "Budget Committee Workshop",
        "url": "https://example.com/videos/budget_workshop.mp4",
        "size_mb": 540,  # 540 MB file
        "quality": "720p"
    },
    {
        "title": "Planning Commission (Full Session)",
        "url": "https://example.com/videos/planning_full.mp4",
        "size_mb": 1240,  # 1.24 GB file
        "quality": "1080p"
    },
    {
        "title": "Mayor's Press Conference",
        "url": "https://example.com/videos/mayor_press.mp4",
        "size_mb": 180,  # 180 MB file
        "quality": "720p"
    }
]

# Network conditions simulation parameters
NETWORK_CONDITIONS = {
    "fast_fiber": {
        "name": "Fast Fiber Connection",
        "base_speed_mbps": 85,  # Base download speed in Mbps
        "fluctuation": 0.15,    # Speed fluctuation factor (±15%)
        "aria2c_improvement": 2.8  # aria2c typically provides 2.8x improvement on fiber
    },
    "cable": {
        "name": "Cable/DSL Connection",
        "base_speed_mbps": 30,  # Base download speed in Mbps
        "fluctuation": 0.25,    # Speed fluctuation factor (±25%)
        "aria2c_improvement": 3.5  # aria2c typically provides 3.5x improvement on cable
    },
    "mobile": {
        "name": "Mobile/LTE Connection",
        "base_speed_mbps": 12,  # Base download speed in Mbps
        "fluctuation": 0.40,    # Speed fluctuation factor (±40%)
        "aria2c_improvement": 4.0  # aria2c typically provides 4.0x improvement on mobile
    }
}

def format_size(size_mb):
    """Format size in MB/GB for display."""
    if size_mb >= 1000:
        return f"{size_mb/1000:.2f} GB"
    else:
        return f"{size_mb:.2f} MB"

def format_speed(speed_mbps):
    """Format speed in Mbps/MBps for display."""
    # Convert Mbps to MBps for easier understanding
    mbps = speed_mbps
    mbps_str = f"{mbps:.2f} Mbps"
    
    # Also show in MB/s (divide by 8 to convert bits to bytes)
    mbytes_per_sec = mbps / 8
    mbytes_str = f"{mbytes_per_sec:.2f} MB/s"
    
    return f"{mbps_str} ({mbytes_str})"

def simulate_download(video, network, use_aria2c=False):
    """
    Simulate a video download with given network parameters.
    
    Args:
        video: Dict containing video information
        network: Dict containing network parameters
        use_aria2c: Whether to simulate aria2c acceleration
        
    Returns:
        dict: Download simulation results
    """
    # Calculate base download speed with random fluctuation
    base_speed = network["base_speed_mbps"]
    fluctuation_factor = 1.0 + random.uniform(-network["fluctuation"], network["fluctuation"])
    current_speed = base_speed * fluctuation_factor
    
    # Apply aria2c improvement if enabled
    if use_aria2c:
        # aria2c effectiveness varies with file size
        if video["size_mb"] < 200:
            # For small files, less effective
            aria2c_factor = network["aria2c_improvement"] * 0.7
        elif video["size_mb"] > 800:
            # For large files, more effective
            aria2c_factor = network["aria2c_improvement"] * 1.2
        else:
            # Medium-sized files
            aria2c_factor = network["aria2c_improvement"]
            
        current_speed *= aria2c_factor
    
    # Calculate download time in seconds (size in MB * 8 bits/byte / speed in Mbps)
    download_time = (video["size_mb"] * 8) / current_speed
    
    # Add some overhead for connection setup, metadata retrieval
    overhead = 2.5 if use_aria2c else 4.0  # aria2c has less overhead for large files
    download_time += overhead
    
    # Return simulation results
    return {
        "title": video["title"],
        "url": video["url"],
        "quality": video["quality"],
        "size_mb": video["size_mb"],
        "size_formatted": format_size(video["size_mb"]),
        "download_speed_mbps": current_speed,
        "download_speed_formatted": format_speed(current_speed),
        "download_time_seconds": download_time,
        "download_time_formatted": f"{download_time:.2f} seconds",
        "used_aria2c": use_aria2c
    }

def simulate_all_downloads(videos, network_type):
    """
    Simulate downloads for all videos with both methods.
    
    Args:
        videos: List of video information dicts
        network_type: Key for the network condition to simulate
        
    Returns:
        dict: Combined simulation results
    """
    network = NETWORK_CONDITIONS[network_type]
    results = []
    
    print(f"\n🌐 Simulating downloads on {network['name']}")
    print(f"   Base speed: {format_speed(network['base_speed_mbps'])}")
    print(f"   Expected aria2c improvement: {network['aria2c_improvement']}x\n")
    
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] Simulating download for: {video['title']} ({video['quality']}, {format_size(video['size_mb'])})")
        
        # Simulate standard yt-dlp download
        print("   ⏳ Standard yt-dlp download...")
        standard_result = simulate_download(video, network, use_aria2c=False)
        
        # Simulate yt-dlp with aria2c download
        print("   ⏳ yt-dlp with aria2c download...")
        aria2c_result = simulate_download(video, network, use_aria2c=True)
        
        # Calculate improvement factor
        speedup = standard_result["download_time_seconds"] / aria2c_result["download_time_seconds"]
        percentage_faster = (speedup - 1) * 100
        
        # Print comparison for this video
        print(f"   📊 Download time comparison:")
        print(f"      yt-dlp:          {standard_result['download_time_formatted']} at {standard_result['download_speed_formatted']}")
        print(f"      yt-dlp + aria2c: {aria2c_result['download_time_formatted']} at {aria2c_result['download_speed_formatted']}")
        print(f"      Speed improvement: {speedup:.2f}x faster ({percentage_faster:.1f}% improvement)")
        
        # Store results
        result = {
            "video": video,
            "yt_dlp": standard_result,
            "aria2c": aria2c_result,
            "speedup": speedup,
            "percentage_faster": percentage_faster
        }
        results.append(result)
    
    # Calculate overall statistics
    total_standard_time = sum(r["yt_dlp"]["download_time_seconds"] for r in results)
    total_aria2c_time = sum(r["aria2c"]["download_time_seconds"] for r in results)
    total_speedup = total_standard_time / total_aria2c_time if total_aria2c_time > 0 else 0
    total_percentage = (total_speedup - 1) * 100 if total_speedup > 0 else 0
    
    avg_speedup = sum(r["speedup"] for r in results) / len(results)
    avg_percentage = sum(r["percentage_faster"] for r in results) / len(results)
    
    # Overall results
    overall = {
        "network_type": network_type,
        "network_name": network["name"],
        "base_speed_mbps": network["base_speed_mbps"],
        "aria2c_improvement_factor": network["aria2c_improvement"],
        "total_videos": len(videos),
        "total_standard_time": total_standard_time,
        "total_aria2c_time": total_aria2c_time,
        "total_speedup": total_speedup,
        "total_percentage_faster": total_percentage,
        "average_speedup": avg_speedup,
        "average_percentage_faster": avg_percentage,
        "detailed_results": results,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return overall

def save_results(results, network_type):
    """Save simulation results to a JSON file."""
    filename = f"simulated_{network_type}_comparison.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed simulation results saved to {filename}")

def print_summary(results):
    """Print a summary of the simulation results."""
    print("\n" + "="*80)
    print("📊 DOWNLOAD SPEED COMPARISON SUMMARY (SIMULATION) 📊".center(80))
    print("="*80)
    print(f"🔹 Network: {results['network_name']}")
    print(f"🔹 Base download speed: {format_speed(results['base_speed_mbps'])}")
    print(f"🔹 Videos simulated: {results['total_videos']}")
    print(f"🔹 Total download time (standard yt-dlp): {results['total_standard_time']:.2f} seconds")
    print(f"🔹 Total download time (yt-dlp + aria2c): {results['total_aria2c_time']:.2f} seconds")
    print(f"🔹 Total time saved: {results['total_standard_time'] - results['total_aria2c_time']:.2f} seconds")
    print(f"🔹 Overall speedup: {results['total_speedup']:.2f}x faster")
    print(f"🔹 Overall percentage improvement: {results['total_percentage_faster']:.1f}%")
    print(f"🔹 Average speedup per video: {results['average_speedup']:.2f}x")
    
    # Print individual video results
    print("\n📑 INDIVIDUAL VIDEO RESULTS:")
    
    for i, result in enumerate(results['detailed_results'], 1):
        video = result['video']
        print(f"\n🔸 [{i}] {video['title']} ({video['quality']}, {format_size(video['size_mb'])})")
        print(f"  • Standard yt-dlp: {result['yt_dlp']['download_time_formatted']} at {result['yt_dlp']['download_speed_formatted']}")
        print(f"  • yt-dlp + aria2c: {result['aria2c']['download_time_formatted']} at {result['aria2c']['download_speed_formatted']}")
        print(f"  • Improvement: {result['speedup']:.2f}x faster ({result['percentage_faster']:.1f}%)")
    
    print("\n" + "="*80)
    print("NOTE: This is a simulation based on typical performance patterns".center(80))
    print("Actual results may vary depending on network conditions and server limitations".center(80))
    print("="*80)

def main():
    """Main function to run the simulation."""
    print("\n🚀 DOWNLOAD SPEED COMPARISON SIMULATION: yt-dlp vs yt-dlp with aria2c\n")
    
    # Create output directory for simulation results
    os.makedirs("simulation_results", exist_ok=True)
    
    # Run simulations for different network conditions
    for network_type in NETWORK_CONDITIONS:
        # Simulate downloads on this network type
        results = simulate_all_downloads(SAMPLE_VIDEOS, network_type)
        
        # Save results to JSON
        save_results(results, network_type)
        
        # Print summary
        print_summary(results)
        
        # Add a separator between network types
        if network_type != list(NETWORK_CONDITIONS.keys())[-1]:
            print("\n" + "-"*80 + "\n")
    
    print("\n✨ Simulation completed! ✨\n")

if __name__ == "__main__":
    main()
