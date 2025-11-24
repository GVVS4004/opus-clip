"""
Lambda Function 4: Process Individual Clip
Extracts clip, converts to 9:16, and adds karaoke subtitles
"""
import json
import boto3
import os
import subprocess

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'opus-clip-videos')

# FFmpeg binary path (should be in /opt/bin via Lambda Layer)
FFMPEG_PATH = os.environ.get('FFMPEG_PATH', '/opt/bin/ffmpeg')

def lambda_handler(event, context):
    """
    Process a single clip

    Input event:
    {
        "session_id": "uuid",
        "s3_video_key": "session_id/original_video.mp4",
        "clip": {
            "clip_index": 0,
            "start": 10.5,
            "end": 40.2,
            "text": "...",
            "segments": [...]
        }
    }

    Output:
    {
        "session_id": "uuid",
        "clip_index": 0,
        "s3_clip_key": "session_id/clips/clip_0.mp4"
    }
    """
    try:
        session_id = event['session_id']
        s3_video_key = event['s3_video_key']
        clip = event['clip']
        clip_index = clip['clip_index']

        print(f"[ProcessClip] Session: {session_id}")
        print(f"[ProcessClip] Clip {clip_index}: {clip['start']:.1f}s - {clip['end']:.1f}s")

        # Download original video from S3
        local_video_path = f"/tmp/{session_id}_original.mp4"
        print(f"[ProcessClip] Downloading video from S3...")
        s3.download_file(BUCKET_NAME, s3_video_key, local_video_path)

        # Extract and convert to 9:16 format
        clip_no_subs_path = f"/tmp/clip_{clip_index}_nosubs.mp4"
        print(f"[ProcessClip] Extracting clip and converting to 9:16...")
        extract_clip_vertical(
            local_video_path,
            clip['start'],
            clip['end'],
            clip_no_subs_path
        )

        # Add karaoke subtitles
        final_clip_path = f"/tmp/clip_{clip_index}.mp4"
        print(f"[ProcessClip] Adding karaoke subtitles...")
        add_karaoke_subtitles(
            clip_no_subs_path,
            clip['segments'],
            clip['start'],
            final_clip_path
        )

        # Upload to S3
        s3_clip_key = f"{session_id}/clips/clip_{clip_index}.mp4"
        print(f"[ProcessClip] Uploading to S3: {s3_clip_key}")
        s3.upload_file(final_clip_path, BUCKET_NAME, s3_clip_key)

        # Clean up temp files
        for path in [local_video_path, clip_no_subs_path, final_clip_path]:
            if os.path.exists(path):
                os.remove(path)

        print(f"[ProcessClip] Complete!")

        return {
            'statusCode': 200,
            'session_id': session_id,
            'clip_index': clip_index,
            's3_clip_key': s3_clip_key
        }

    except Exception as e:
        print(f"[ProcessClip] Error: {str(e)}")
        raise Exception(f"Failed to process clip: {str(e)}")


def extract_clip_vertical(video_path, start_time, end_time, output_path):
    """Extract clip and convert to 9:16 vertical format"""
    duration = end_time - start_time
    target_width = 1080
    target_height = 1920

    cmd = [
        FFMPEG_PATH,
        '-ss', str(start_time),
        '-i', video_path,
        '-t', str(duration),
        '-vf', f'scale=-2:{target_height},crop={target_width}:{target_height}:(iw-{target_width})/2:0',
        '-c:v', 'libx264',
        '-preset', 'faster',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-avoid_negative_ts', 'make_zero',
        '-y',
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg extraction failed: {result.stderr}")

    return output_path


def add_karaoke_subtitles(video_path, segments, clip_start, output_path):
    """Add karaoke-style word-by-word subtitles"""
    # Create ASS subtitle file
    ass_path = video_path.replace('.mp4', '.ass')
    create_karaoke_ass(segments, clip_start, ass_path)

    # Fix path for FFmpeg (handle Windows-style paths on Lambda)
    ass_path_ffmpeg = ass_path.replace('\\', '/').replace(':', '\\:')

    cmd = [
        FFMPEG_PATH,
        '-i', video_path,
        '-vf', f"ass={ass_path_ffmpeg}",
        '-c:v', 'libx264',
        '-preset', 'faster',
        '-crf', '23',
        '-c:a', 'copy',
        '-y',
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg subtitle encoding failed: {result.stderr}")

    # Clean up ASS file
    if os.path.exists(ass_path):
        os.remove(ass_path)

    return output_path


def create_karaoke_ass(segments, clip_start, output_path):
    """Create ASS file with karaoke word-by-word highlighting"""
    # ASS header
    ass_content = """[Script Info]
Title: Karaoke Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,50,50,200,1
Style: Highlight,Arial,60,&H0000FF00,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,50,50,200,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []

    # Process each segment
    for segment in segments:
        words = segment.get('words', [])

        if not words:
            # Fallback if no word-level timestamps
            start = segment['start'] - clip_start
            end = segment['end'] - clip_start
            text = segment['text'].strip()
            events.append(f"Dialogue: 0,{format_time(start)},{format_time(end)},Default,,0,0,0,,{text}")
            continue

        # Group words into chunks (3 words per line for readability)
        chunk_size = 3
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]

            if not chunk_words:
                continue

            # Time range for this chunk
            chunk_start = chunk_words[0]['start'] - clip_start
            chunk_end = chunk_words[-1]['end'] - clip_start

            # Create karaoke effect for each word in chunk
            for word_obj in chunk_words:
                word_start = word_obj['start'] - clip_start
                word_end = word_obj['end'] - clip_start
                word_text = word_obj['word'].strip()

                # Show all words, highlight current word
                display_words = []
                for w in chunk_words:
                    w_text = w['word'].strip()
                    if w == word_obj:
                        # Current word - highlighted (green)
                        display_words.append(f"{{\\c&H00FF00&}}{w_text}{{\\c}}")
                    else:
                        # Other words - white
                        display_words.append(w_text)

                line_text = ' '.join(display_words)
                events.append(f"Dialogue: 0,{format_time(word_start)},{format_time(word_end)},Default,,0,0,0,,{line_text}")

    ass_content += '\n'.join(events)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)


def format_time(seconds):
    """Format seconds to ASS timestamp (H:MM:SS.CC)"""
    if seconds < 0:
        seconds = 0

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)

    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
