"""
Lambda Function 2: Transcribe Video using Whisper
Handles audio transcription with word-level timestamps
"""
import json
import boto3
import os
import whisper

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'opus-clip-videos')

# Load Whisper model once (reused across warm invocations)
model = None
MODEL_SIZE = os.environ.get('WHISPER_MODEL', 'base')

def lambda_handler(event, context):
    """
    Transcribe video using OpenAI Whisper

    Input event:
    {
        "session_id": "uuid",
        "s3_video_key": "session_id/original_video.mp4",
        "video_info": {...}
    }

    Output:
    {
        "session_id": "uuid",
        "s3_video_key": "...",
        "s3_transcript_key": "session_id/transcript.json",
        "video_info": {...}
    }
    """
    global model

    try:
        session_id = event['session_id']
        s3_video_key = event['s3_video_key']
        video_info = event.get('video_info', {})

        print(f"[Transcribe] Session: {session_id}")
        print(f"[Transcribe] Video: {s3_video_key}")

        # Download video from S3
        local_video_path = f"/tmp/{session_id}_video.mp4"
        print(f"[Transcribe] Downloading from S3...")
        s3.download_file(BUCKET_NAME, s3_video_key, local_video_path)

        # Load Whisper model (cached on warm starts)
        if model is None:
            print(f"[Transcribe] Loading Whisper '{MODEL_SIZE}' model...")
            model = whisper.load_model(MODEL_SIZE)
            print("[Transcribe] Model loaded!")
        else:
            print("[Transcribe] Using cached model")

        # Transcribe with word-level timestamps
        print("[Transcribe] Transcribing audio...")
        result = model.transcribe(
            local_video_path,
            word_timestamps=True,
            verbose=False
        )

        # Extract segments with timestamps
        segments = []
        for segment in result.get('segments', []):
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'words': segment.get('words', [])
            })

        transcript_data = {
            'text': result['text'],
            'segments': segments,
            'language': result.get('language', 'unknown')
        }

        print(f"[Transcribe] Transcribed {len(segments)} segments")
        print(f"[Transcribe] Language: {transcript_data['language']}")

        # Upload transcript to S3
        transcript_key = f"{session_id}/transcript.json"
        print(f"[Transcribe] Uploading transcript to S3: {transcript_key}")

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=transcript_key,
            Body=json.dumps(transcript_data, ensure_ascii=False, indent=2),
            ContentType='application/json'
        )

        # Clean up local file
        os.remove(local_video_path)
        print("[Transcribe] Complete!")

        return {
            'statusCode': 200,
            'session_id': session_id,
            's3_video_key': s3_video_key,
            's3_transcript_key': transcript_key,
            'video_info': video_info
        }

    except Exception as e:
        print(f"[Transcribe] Error: {str(e)}")
        raise Exception(f"Failed to transcribe video: {str(e)}")
