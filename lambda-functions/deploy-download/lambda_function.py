"""
Lambda Function 1: Download Video from YouTube
Handles downloading YouTube video and uploading to S3
"""
import json
import boto3
import os
import sys
from pytubefix import YouTube
from pytubefix.exceptions import PytubeFixError

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'opus-clip-videos')

def lambda_handler(event, context):
    """
    Download YouTube video and upload to S3

    Input event:
    {
        "session_id": "uuid",
        "youtube_url": "https://www.youtube.com/watch?v=..."
    }

    Output:
    {
        "session_id": "uuid",
        "s3_video_key": "session_id/original_video.mp4",
        "video_info": {...}
    }
    """
    try:
        session_id = event['session_id']
        youtube_url = event['youtube_url']

        print(f"[Download] Session: {session_id}")
        print(f"[Download] URL: {youtube_url}")

        # Clean URL
        if '&' in youtube_url and 'v=' in youtube_url:
            video_id = youtube_url.split('v=')[1].split('&')[0]
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"[Download] Cleaned URL: {youtube_url}")

        # Fetch video information
        print("[Download] Fetching video info...")
        yt = YouTube(youtube_url)

        video_info = {
            'title': yt.title,
            'duration': yt.length,
            'description': yt.description or '',
            'uploader': yt.author,
            'view_count': yt.views or 0,
            'thumbnail_url': yt.thumbnail_url
        }

        print(f"[Download] Title: {video_info['title']}")
        print(f"[Download] Duration: {video_info['duration']} seconds")

        # Check duration limit (1 hour max)
        if video_info['duration'] > 3600:
            raise Exception("Video duration exceeds 1 hour limit")

        # Select best progressive stream
        print("[Download] Selecting stream...")
        stream = yt.streams.filter(
            progressive=True,
            file_extension='mp4'
        ).order_by('resolution').desc().first()

        if not stream:
            stream = yt.streams.filter(progressive=True).first()

        if not stream:
            raise Exception("No suitable video streams found")

        print(f"[Download] Selected: {stream.resolution} - {stream.mime_type}")

        # Download to Lambda /tmp directory
        tmp_dir = '/tmp'
        output_filename = f"{session_id}_video.mp4"
        local_path = os.path.join(tmp_dir, output_filename)

        print(f"[Download] Downloading to {local_path}...")
        stream.download(output_path=tmp_dir, filename=output_filename)

        # Upload to S3
        s3_key = f"{session_id}/original_video.mp4"
        print(f"[Download] Uploading to S3: {s3_key}")

        s3.upload_file(local_path, BUCKET_NAME, s3_key)

        # Clean up local file
        os.remove(local_path)
        print("[Download] Complete!")

        return {
            'statusCode': 200,
            'session_id': session_id,
            's3_video_key': s3_key,
            'video_info': video_info
        }

    except PytubeFixError as e:
        print(f"[Download] Pytube error: {str(e)}")
        raise Exception(f"Failed to download video: {str(e)}")
    except Exception as e:
        print(f"[Download] Error: {str(e)}")
        raise Exception(f"Failed to download video: {str(e)}")
