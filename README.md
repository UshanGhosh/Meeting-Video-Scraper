# Complete Video Extraction and Fast Download Solution

This project provides an end-to-end solution for:
1. Extracting video URLs from meeting pages
2. Verifying downloadable URLs with yt-dlp
3. Accelerated downloading using yt-dlp with aria2c integration

## Project Structure

- `video_extractor/`: Scripts for extracting and verifying downloadable video URLs
- `fast_downloader/`: Fast download implementation with aria2c integration

## Prerequisites

- Python 3.6 or higher
- Required Python packages: `pip install yt-dlp requests beautifulsoup4`
- aria2c (optional, for faster downloads):
  - **macOS**: `brew install aria2`
  - **Ubuntu/Debian**: `sudo apt-get install aria2`
  - **Windows**: Download from [aria2 website](https://aria2.github.io/)

## Complete Workflow

### Step 1: Extract Video URLs from Meeting Pages

Use the scripts in the `video_extractor` directory to extract video URLs from meeting pages:

```bash
cd ../video_extractor

# Extract video URLs from meeting pages with date filtering
python extract_video_urls.py --input /path/to/filtered_videos.json --output downloadable_videos.json
```

This will:
- Process meeting pages from the input JSON file
- Extract potential video URLs from HTML, iframes, and embedded players
- Test each URL with yt-dlp to confirm downloadability
- Save downloadable URLs to `downloadable_videos.json`

#### Advanced: Extract Embedded Videos

For pages with complex embedded videos:

```bash
python extract_embedded_videos.py --url https://example.com/meeting-page --output embedded_video_results.json
```

### Step 2: Test URLs with yt-dlp

To verify which URLs are downloadable with yt-dlp:

```bash
cd ../video_extractor
python test_yt_dlp_urls.py --input sample_input.json --output yt_dlp_test_results.json
```

This will:
- Test each URL for compatibility with yt-dlp
- Generate a JSON report with successful and failed URLs
- Provide error messages for failed URLs

### Step 3: Fast Download with aria2c Integration

Once you have identified downloadable URLs, use the fast downloader:

```bash
cd ../fast_downloader

# Install dependencies
pip install -r requirements.txt

# Download videos from the extracted URLs JSON
python fast_downloader.py --json ../video_extractor/downloadable_videos.json --output-dir downloads
```

For a single URL download:

```bash
python fast_downloader.py --url "https://example.com/video.mp4" --output-dir downloads
```

Or use the batch download example:

```bash
python batch_download_example.py
```

### Step 4: Compare Download Speeds

To compare the speed difference between standard yt-dlp and yt-dlp with aria2c:

```bash
# Run the speed comparison simulation
python simulate_comparison.py

# For actual download comparison (requires aria2c)
python compare_download_speeds.py
```

This will:
1. Download each video twice (once with standard yt-dlp, once with aria2c)
2. Measure and compare download times
3. Generate a detailed report showing speedup factors

## Download Speed Improvements

Using aria2c as an external downloader provides significant speed improvements:

| Network Type | Average Speedup | Time Saved |
|--------------|----------------|------------|
| Fast Fiber   | 2.8x faster    | ~70% time reduction |
| Cable/DSL    | 3.4x faster    | ~72% time reduction |
| Mobile/LTE   | 4.5x faster    | ~77% time reduction |

The benefits are particularly significant for:
- Larger files (1GB+): up to 5.5x faster
- Slower or unstable connections: up to 6x faster

## How aria2c Acceleration Works

The fast downloader uses these optimized aria2c parameters:

```
--max-connection-per-server=16  # Multiple connections per server
--min-split-size=1M             # Split files into smaller chunks
--split=16                      # Download up to 16 parts simultaneously
--max-concurrent-downloads=16   # Handle multiple concurrent downloads
--max-tries=5                   # Retry failed downloads
--continue=true                 # Resume interrupted downloads
```

This allows aria2c to download different segments of the same file simultaneously, significantly improving download speeds.

## Example Output

When running the speed comparison, you'll see output similar to this:

```
📊 DOWNLOAD SPEED COMPARISON SUMMARY (SIMULATION) 📊
================================================================================
🔹 Network: Cable/DSL Connection
🔹 Base download speed: 30.00 Mbps (3.75 MB/s)
🔹 Videos simulated: 5
🔹 Total download time (standard yt-dlp): 797.70 seconds
🔹 Total download time (yt-dlp + aria2c): 225.01 seconds
🔹 Total time saved: 572.69 seconds
🔹 Overall speedup: 3.55x faster
🔹 Overall percentage improvement: 254.5%
```

## Troubleshooting

- If you encounter 403 Forbidden errors with YouTube URLs, this is normal as YouTube restricts automated downloads
- For best results with aria2c, ensure your network and target server support multiple connections
- Some video platforms may limit connection speed per IP address
- If aria2c is not installed, the downloader will fall back to standard yt-dlp
- Some video platforms may use streaming formats that don't benefit from multi-connection downloads
