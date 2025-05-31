#!/usr/bin/env python3
"""
Filter videos from all_videos.json by date range and save to a new JSON file.
"""
import json
import os
import re
import sys
from datetime import datetime

def filter_videos_by_date(start_date, end_date, input_file="output/all_videos.json", output_file="output/filtered_videos.json"):
    # Convert start and end dates to datetime objects
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format. Please use YYYY-MM-DD format.")
        return 0
    
    print(f"Filtering videos between {start_date} and {end_date}...")
    
    # Read the input JSON file
    try:
        with open(input_file, 'r') as f:
            all_sources = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading input file: {e}")
        return 0
    
    # Create output structure
    filtered_sources = []
    total_filtered_videos = 0
    
    # Process each source
    for source in all_sources:
        # Handle individual media entries (direct URL entries)
        if "url" in source and "date" in source:
            date_str = source.get("date", "Unknown")
            
            # Skip entries with unknown dates
            if date_str == "Unknown":
                continue
            
            # Make sure date_str is a string before using re.match
            if not isinstance(date_str, str):
                continue
                
            # Fix malformed dates (e.g., "025-52-82" should be ignored)
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                continue
            
            try:
                video_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                # Check if the video date is within the specified range
                if start <= video_date <= end:
                    filtered_sources.append(source)
                    total_filtered_videos += 1
            except ValueError:
                # Skip videos with invalid dates
                continue
        # Process sources with base_url and medias
        elif "base_url" in source and "medias" in source:
            base_url = source.get("base_url", "Unknown source")
            medias = source.get("medias", [])
            
            # Filter videos by date
            filtered_medias = []
            
            for video in medias:
                date_str = video.get("date", "Unknown")
                
                # Skip videos with unknown dates
                if date_str == "Unknown":
                    continue
                
                # Make sure date_str is a string before using re.match
                if not isinstance(date_str, str):
                    continue
                    
                # Fix malformed dates (e.g., "025-52-82" should be ignored)
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                    continue
                
                try:
                    video_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Check if the video date is within the specified range
                    if start <= video_date <= end:
                        filtered_medias.append(video)
                except ValueError:
                    # Skip videos with invalid dates
                    continue
            
            # Only include sources with filtered videos
            if filtered_medias:
                filtered_sources.append({
                    "base_url": base_url,
                    "medias": filtered_medias
                })
                total_filtered_videos += len(filtered_medias)
    
    # Save the filtered videos to the output file
    if total_filtered_videos > 0:
        try:
            # Create the output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(filtered_sources, f, indent=2)
                
            print(f"Successfully saved {total_filtered_videos} filtered videos to {output_file}")
        except Exception as e:
            print(f"Error saving output file: {e}")
    else:
        print("No videos found within the specified date range.")
    
    return total_filtered_videos

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python filter_videos_by_date.py START_DATE END_DATE [INPUT_FILE] [OUTPUT_FILE]")
        print("Example: python filter_videos_by_date.py 2025-01-01 2025-03-31")
        sys.exit(1)
    
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    
    input_file = sys.argv[3] if len(sys.argv) > 3 else "output/all_videos.json"
    output_file = sys.argv[4] if len(sys.argv) > 4 else "output/filtered_videos.json"
    
    filter_videos_by_date(start_date, end_date, input_file, output_file)