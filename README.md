# Meeting Video Extractor and Fast Downloader

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

A complete solution for extracting, verifying, and efficiently downloading video content from local government meeting pages.

## Features

- 🔍 **Intelligent Extraction**: Identifies and extracts video URLs from various meeting pages
- 📅 **Date Filtering**: Filters videos by specific date ranges
- ✅ **Downloadability Verification**: Tests URLs with yt-dlp to confirm they're downloadable
- ⚡ **Accelerated Downloads**: Integrates yt-dlp with aria2c for multi-threaded downloading
- 📊 **Performance Metrics**: Compares download speeds between methods

## Project Structure

```
├── scrapers/         # Individual website scrapers
├── video_extractor/  # URL extraction and verification
├── fast_downloader/  # Accelerated download implementation
├── output/           # Extracted URL JSON files
└── main.py           # Main execution script
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/meeting-video-extractor.git
cd meeting-video-extractor

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Install aria2c (optional, for faster downloads)
# macOS
brew install aria2
# Ubuntu/Debian
sudo apt-get install aria2
# Windows: Download from https://aria2.github.io/
```

## Complete Workflow

### 1. Extract Videos from Websites

Run the main script to scrape all supported websites:

```bash
python main.py
```

This extracts videos from:
- Lansdale.org Council Meetings
- Dauphin County Facebook Videos
- Charleston WV Civic Clerk Portal
- Salt Lake City YouTube Channel
- Regional Web TV
- Winchester VA Civic Web Portal

Output files are saved to the `output/` directory.

### 2. Filter Videos by Date (Optional)

Filter the extracted videos by date range:

```bash
python date_filter.py --input output/all_videos.json --start 2023-01-01 --end 2023-12-31 --output output/filtered_videos.json
```

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
cd fast_downloader
python fast_downloader.py --url "https://example.com/video.mp4" --output-dir downloads
```

## Download Acceleration Technology

The fast downloader uses optimized aria2c parameters to significantly improve download speeds:

```
--max-connection-per-server=16  # Multiple connections per server
--min-split-size=1M             # Split files into smaller chunks
--split=16                      # Download up to 16 parts simultaneously
--max-concurrent-downloads=16   # Handle multiple concurrent downloads
--max-tries=5                   # Retry failed downloads
--continue=true                 # Resume interrupted downloads
```

### Acceleration Features

- **Multi-connection downloads**: Downloads different segments of the same file simultaneously
- **Batch processing**: Handles multiple videos sequentially
- **Comprehensive logging**: Records download times and performance metrics

## Troubleshooting

- If you encounter 403 Forbidden errors with YouTube URLs, this is normal as YouTube restricts automated downloads
- For best results with aria2c, ensure your network and target server support multiple connections
- Some video platforms may limit connection speed per IP address
- If aria2c is not installed, the downloader will fall back to standard yt-dlp

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
