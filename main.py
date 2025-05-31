#!/usr/bin/env python3
"""
Main script for government website video scraper
Collects videos from multiple sources and filters them by date
"""

import os
import json
import sys
from datetime import datetime
import importlib
import glob
from filter_videos_by_date import filter_videos_by_date

# Dates to filter videos (edit these values to change date range)
START_DATE = "2024-11-01"
END_DATE = "2024-12-31"

def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    if not os.path.exists("output"):
        os.makedirs("output")

def run_scrapers():
    """Run all scrapers and collect their output files"""
    print("Running video scrapers...")
    
    # Get all scraper modules in the scrapers directory
    scrapers_dir = os.path.join(os.path.dirname(__file__), "scrapers")
    sys.path.insert(0, scrapers_dir)
    
    for file in glob.glob(os.path.join(scrapers_dir, "*.py")):
        if os.path.basename(file) == "__init__.py":
            continue
        
        module_name = os.path.basename(file)[:-3]  # Remove .py extension
        try:
            module = importlib.import_module(f"scrapers.{module_name}")
            if hasattr(module, "run"):
                print(f"Running {module_name} scraper...")
                module.run()
        except Exception as e:
            print(f"Error running {module_name} scraper: {e}")

def combine_all_videos():
    """Combine all individual video JSON files into one all_videos.json file"""
    print("Combining video data...")
    all_sources = []
    
    for file in glob.glob("output/*_videos.json"):
        if file == "output/all_videos.json" or file == "output/filtered_videos.json":
            continue
            
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_sources.extend(data)
                else:
                    all_sources.append(data)
        except Exception as e:
            print(f"Error processing {file}: {e}")
    
    with open("output/all_videos.json", 'w') as f:
        json.dump(all_sources, f, indent=2)
    
    return len(all_sources)

def main():
    """Main entry point for the video scraper and filter application"""
    ensure_output_dir()
    
    # Run all scrapers to collect video data
    run_scrapers()
    
    # Combine all individual video files into one
    sources_count = combine_all_videos()
    print(f"Combined {sources_count} sources into all_videos.json")
    
    # Filter videos by date range
    filtered_count = filter_videos_by_date(
        START_DATE, 
        END_DATE, 
        "output/all_videos.json", 
        "output/filtered_videos.json"
    )
    
    print(f"Filtered {filtered_count} videos between {START_DATE} and {END_DATE}")
    print(f"Results saved to output/filtered_videos.json")

if __name__ == "__main__":
    main()
