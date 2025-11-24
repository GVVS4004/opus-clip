"""
Video Downloader Module - Cloud Optimized
Downloads videos from YouTube using pytubefix (more reliable on cloud servers)
"""
import os
from pytubefix import YouTube
from pytubefix.exceptions import PytubeFixError
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoDownloaderCloud:
    def __init__(self, download_dir='downloads'):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

    def download_video(self, url, output_filename='video'):
        """
        Download video from YouTube URL using pytubefix

        Args:
            url: YouTube video URL
            output_filename: Base name for output file (without extension)

        Returns:
            tuple: (video_path, video_info)
        """
        try:
            # Clean URL - remove query parameters except v=
            if '&' in url:
                # Extract just the video ID
                if 'v=' in url:
                    video_id = url.split('v=')[1].split('&')[0]
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    logger.info(f"Cleaned URL to: {url}")

            logger.info(f"Fetching video information from: {url}")

            # Create YouTube object
            yt = YouTube(url)

            # Get video information
            video_info = {
                'title': yt.title,
                'duration': yt.length,
                'description': yt.description or '',
                'uploader': yt.author,
                'view_count': yt.views or 0,
                'thumbnail_url': yt.thumbnail_url
            }

            logger.info(f"Title: {video_info['title']}")
            logger.info(f"Duration: {video_info['duration']} seconds")

            # Get the highest resolution progressive stream (video+audio combined)
            # Progressive = video and audio in one file (easier to process)
            logger.info("Selecting best available stream...")

            # Try to get 720p or best available
            stream = yt.streams.filter(
                progressive=True,
                file_extension='mp4'
            ).order_by('resolution').desc().first()

            if not stream:
                # Fallback: get any progressive stream
                stream = yt.streams.filter(progressive=True).first()

            if not stream:
                # Last resort: get highest resolution stream and audio separately
                video_stream = yt.streams.filter(
                    only_video=True,
                    file_extension='mp4'
                ).order_by('resolution').desc().first()

                audio_stream = yt.streams.filter(
                    only_audio=True
                ).first()

                if video_stream and audio_stream:
                    logger.warning("Progressive stream not available, will need to merge video and audio")
                    return self._download_and_merge(video_stream, audio_stream, output_filename, video_info)
                else:
                    raise Exception("No suitable video streams found")

            logger.info(f"Selected stream: {stream.resolution} - {stream.mime_type}")

            # Download the video
            logger.info(f"Downloading to: {self.download_dir}")
            output_path = stream.download(
                output_path=self.download_dir,
                filename=f"{output_filename}.mp4"
            )

            logger.info(f"✓ Download complete: {output_path}")

            return output_path, video_info

        except PytubeFixError as e:
            logger.error(f"Pytube error: {str(e)}")
            raise Exception(f"Failed to download video: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"Failed to download video: {str(e)}")

    def _download_and_merge(self, video_stream, audio_stream, output_filename, video_info):
        """
        Download video and audio separately and merge using ffmpeg
        """
        import subprocess

        logger.info("Downloading video stream...")
        video_path = video_stream.download(
            output_path=self.download_dir,
            filename=f"{output_filename}_video.mp4"
        )

        logger.info("Downloading audio stream...")
        audio_path = audio_stream.download(
            output_path=self.download_dir,
            filename=f"{output_filename}_audio.mp4"
        )

        # Merge using ffmpeg
        output_path = os.path.join(self.download_dir, f"{output_filename}.mp4")
        logger.info("Merging video and audio...")

        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"FFmpeg merge failed: {result.stderr}")

        # Clean up temporary files
        try:
            os.remove(video_path)
            os.remove(audio_path)
        except:
            pass

        logger.info(f"✓ Merge complete: {output_path}")

        return output_path, video_info

    def get_video_info(self, url):
        """
        Get video information without downloading

        Args:
            url: YouTube video URL

        Returns:
            dict: Video information
        """
        try:
            yt = YouTube(url)

            return {
                'title': yt.title,
                'duration': yt.length,
                'description': yt.description or '',
                'uploader': yt.author,
                'view_count': yt.views or 0,
                'thumbnail_url': yt.thumbnail_url
            }
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")

    def cleanup_downloads(self, keep_latest=5):
        """
        Clean up old downloads to save disk space

        Args:
            keep_latest: Number of most recent downloads to keep
        """
        try:
            files = []
            for f in os.listdir(self.download_dir):
                if f.endswith('.mp4'):
                    filepath = os.path.join(self.download_dir, f)
                    files.append((filepath, os.path.getmtime(filepath)))

            # Sort by modification time (newest first)
            files.sort(key=lambda x: x[1], reverse=True)

            # Delete old files
            for filepath, _ in files[keep_latest:]:
                try:
                    os.remove(filepath)
                    logger.info(f"Cleaned up: {filepath}")
                except:
                    pass

        except Exception as e:
            logger.warning(f"Cleanup warning: {str(e)}")


if __name__ == '__main__':
    # Test the downloader
    downloader = VideoDownloaderCloud()
    url = input("Enter YouTube URL: ")
    print("Downloading video...")
    video_path, info = downloader.download_video(url)
    print(f"Downloaded to: {video_path}")
    print(f"Title: {info.get('title', 'Unknown')}")
