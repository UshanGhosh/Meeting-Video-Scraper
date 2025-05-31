# Video URL Extractor

This tool extracts direct video URLs from meeting pages that can be downloaded using yt-dlp.

## 🧩 Objective

Extract direct video URLs from scraped meeting pages to be used by [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading.

The tool:
- Reads URLs from the input JSON file
- Visits webpages with embedded players 
- Locates and extracts the downloadable video source URLs
- Verifies each URL with yt-dlp
- Saves only downloadable URLs to a new JSON file

## 📋 Prerequisites

- Python 3.6+
- yt-dlp must be installed (`pip install yt-dlp`)
- Required Python packages:
  - requests
  - beautifulsoup4

Install dependencies:
```
pip install yt-dlp requests beautifulsoup4
```

## 🚀 Usage

Run the script from the video_extractor directory:

```bash
cd /path/to/video_extractor
python extract_video_urls.py
```

## 📄 Input/Output

- **Input**: The script reads URLs from `../output/filtered_videos.json`
- **Outputs**:
  - `downloadable_videos.json` - List of video URLs that can be downloaded with yt-dlp
  - `sample_input.json` - A copy of the input URLs for reference
  - `video_extractor.log` - Detailed log of the extraction process

## 💡 How It Works

1. The script first checks if each URL is directly downloadable with yt-dlp
2. If not, it visits the webpage and extracts potential video sources:
   - Direct video tags and sources
   - Iframe embeds
   - JSON data containing video URLs
   - Common video URL patterns
   - Download links
3. Each potential video URL is verified with yt-dlp
4. Only working downloadable URLs are saved to the output file
