# Meeting Video Extractor and Fast Downloader

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

A comprehensive solution for extracting, verifying, and fast-downloading video content from local government meeting pages.

## Features

- **Video URL Extraction**: Scrapes government meeting pages to find video content
- **Date Filtering**: Extracts only videos from meetings within a specified date range
- **Downloadability Verification**: Tests URLs with yt-dlp to confirm they're downloadable
- **Fast Downloading**: Uses aria2c integration for multi-threaded accelerated downloads
- **Embedded Video Support**: Extracts videos from complex embedded players
- **Speed Comparison**: Provides detailed metrics on download speed improvements

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/meeting-video-extractor.git
cd meeting-video-extractor

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (if using Playwright scrapers)
playwright install

# Optional: Install aria2c for accelerated downloads
# macOS: brew install aria2
# Ubuntu/Debian: sudo apt-get install aria2
# Windows: Download from https://aria2.github.io/
```

## Complete Workflow

### 1. Extract Video URLs from Meeting Pages

```bash
# Run the main scraper with date filtering
python main.py --start-date "2023-01-01" --end-date "2023-12-31" --output output/filtered_videos.json
```

This process:
- Scrapes meeting pages from various government websites
- Filters meetings by date range
- Identifies video URLs for each meeting
- Outputs a structured JSON file

### 2. Individual Website Scrapers

Run specific website scrapers individually:

```bash
python -m scrapers.lansdale
python -m scrapers.dauphin_county
# etc.
```

These scrapers:
- Use Playwright for dynamic page loading
- Implement XPath locators for consistent video extraction
- Handle pagination and listing pages
- Support concurrent processing for faster extraction

### 3. Verify Downloadable URLs

Test which URLs are downloadable with yt-dlp:

```bash
cd video_extractor
python extract_video_urls.py --input ../output/filtered_videos.json --output downloadable_videos.json
```

This process:
- Tests each URL for compatibility with yt-dlp
- Identifies downloadable video sources
- Outputs a JSON file with verified downloadable URLs
- Filters out non-downloadable URLs with appropriate error messages

### 4. Fast Download with aria2c

Download the verified videos with accelerated speeds:

```bash
cd ../fast_downloader
python fast_downloader.py --json ../video_extractor/downloadable_videos.json --output-dir downloads
```

### 5. Compare Download Speeds (Optional)

Compare the performance between standard yt-dlp and aria2c-accelerated downloads:

```bash
# Run simulation (no actual downloads)
python simulate_comparison.py

# Or perform real download comparison
python compare_download_speeds.py
```

## Advanced Usage

### Individual Website Scrapers

Run specific website scrapers individually:

```bash
python -m scrapers.lansdale
python -m scrapers.dauphin_county
# etc.
```

### Extract Embedded Videos

For complex embedded videos on specific pages:

```bash
cd video_extractor
python extract_embedded_videos.py --url "https://example.com/meeting-page"
```

### Single URL Download

Download a specific video URL:

```bash
cd faster_download
python fast_downloader.py --url "https://example.com/video.mp4" --output-dir downloads
```

## Download Acceleration Technology

The fast downloader uses optimized aria2c parameters to significantly improve download speeds:

```
--max-connection-per-server=16  # Multiple connections per server
--min-split-size=1M             # Split files for parallel downloading
--split=16                      # Number of splits per file
--max-concurrent-downloads=16   # Number of parallel downloads
--max-tries=5                   # Retry count for failed downloads
--continue=true                 # Resume interrupted downloads
```

### Acceleration Features

- **Multi-connection downloads**: Downloads different segments of the same file simultaneously
- **Batch processing**: Handles multiple videos sequentially
- **Comprehensive logging**: Records download times and performance metrics


## Troubleshooting

- YouTube and similar platforms may return HTTP 403 errors due to download restrictions
- For best results with aria2c, ensure your network and target server support multiple connections
- Some video platforms may limit connection speed per IP address
- If aria2c is not installed, the downloader will fall back to standard yt-dlp
- Some video platforms may use streaming formats that don't benefit from multi-connection downloads


## Demo Video

[![Meeting Video Extractor Demo](https://img.youtube.com/vi/DA5Q_00pqL8/0.jpg)](https://www.youtube.com/watch?v=DA5Q_00pqL8)

*Click on the image above to watch the demonstration video*


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
