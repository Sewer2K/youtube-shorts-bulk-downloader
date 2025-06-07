import yt_dlp
import os


def get_short_links(channel_url):
    """Extract Shorts video links from a YouTube channel."""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlist_end': 100,  # Fetch up to 100 videos
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(channel_url, download=False)
        if 'entries' in result:
            video_ids = [entry['id'] for entry in result['entries']]
            short_links = [f'https://www.youtube.com/shorts/{video_id}' for video_id in video_ids]
            return short_links
        else:
            print("No Shorts videos found.")
            return []


def download_videos_from_links(links, output_path, cookies_path):
    """Download videos from the list of links."""
    total_links = len(links)

    print(f"Using cookies from: {cookies_path}")
    for index, link in enumerate(links, start=1):
        link = link.strip()
        try:
            ydl_opts = {
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'format': 'best',
                'noplaylist': True,
                'quiet': False,
                'ignoreerrors': True,
                'cookiefile': cookies_path,  # Load cookies from the file
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
                'headers': {
                    'Accept-Language': 'en-US,en;q=0.9',
                },
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            print(f"Downloaded video {index}/{total_links}: {link}")
        except Exception as e:
            print(f"Error downloading {link}: {e}")
        finally:
            progress = int((index / total_links) * 100)
            print(f"Progress: {progress}%")


def main():
    """Main function for command-line execution."""
    # Hardcoded channel URL
    channel_url = "https://www.youtube.com/@DriftNinjaRC"

    # Path to cookies.txt
    cookies_path = "cookies.txt"  # Ensure this file exists

    # Default output directory
    output_path = "downloaded_videos"

    # Create the output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    # Extract Shorts video links
    print(f"Fetching Shorts video links from {channel_url}...")
    short_links = get_short_links(channel_url)
    if not short_links:
        print("No Shorts videos found.")
        return

    # Download the videos
    print(f"Found {len(short_links)} Shorts videos. Starting download...")
    download_videos_from_links(short_links, output_path, cookies_path)
    print(f"Download process completed! Videos saved in: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
