"""
Lambda Function 3: Detect Viral Clips
Analyzes transcript and identifies potential viral clip segments
"""
import json
import boto3
import os
import re

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'opus-clip-videos')

# Clip detection settings
MIN_CLIP_DURATION = int(os.environ.get('MIN_CLIP_DURATION', '15'))
MAX_CLIP_DURATION = int(os.environ.get('MAX_CLIP_DURATION', '60'))
TARGET_CLIP_DURATION = int(os.environ.get('TARGET_CLIP_DURATION', '30'))
NUM_CLIPS = int(os.environ.get('NUM_CLIPS', '3'))

# Viral keywords
VIRAL_KEYWORDS = [
    'secret', 'hack', 'tip', 'trick', 'amazing', 'incredible',
    'shocking', 'revealed', 'how to', 'why', 'never', 'always',
    'mistake', 'avoid', 'best', 'worst', 'truth', 'nobody',
    'everyone', 'simple', 'easy', 'quick', 'fast', 'powerful',
    'changed', 'transform', 'learn', 'discover', 'found',
    'story', 'crazy', 'insane', 'genius', 'strategy'
]

def lambda_handler(event, context):
    """
    Detect viral clips from transcript

    Input event:
    {
        "session_id": "uuid",
        "s3_video_key": "...",
        "s3_transcript_key": "session_id/transcript.json",
        "video_info": {...}
    }

    Output:
    {
        "session_id": "uuid",
        "s3_video_key": "...",
        "clips": [
            {
                "clip_index": 0,
                "start": 10.5,
                "end": 40.2,
                "duration": 29.7,
                "text": "...",
                "segments": [...],
                "score": 85.5
            }
        ],
        "video_info": {...}
    }
    """
    try:
        session_id = event['session_id']
        s3_video_key = event['s3_video_key']
        transcript_key = event['s3_transcript_key']
        video_info = event.get('video_info', {})

        print(f"[Detect] Session: {session_id}")
        print(f"[Detect] Transcript: {transcript_key}")

        # Download transcript from S3
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=transcript_key)
        transcript_data = json.loads(obj['Body'].read())
        segments = transcript_data['segments']

        print(f"[Detect] Analyzing {len(segments)} segments...")

        # Detect clip candidates
        candidates = []
        for i in range(len(segments)):
            for j in range(i + 1, len(segments) + 1):
                clip_start = segments[i]['start']
                clip_end = segments[j - 1]['end']
                duration = clip_end - clip_start

                # Check duration constraints
                if duration < MIN_CLIP_DURATION:
                    continue
                if duration > MAX_CLIP_DURATION:
                    break

                # Extract text for this clip
                clip_text = ' '.join([seg['text'] for seg in segments[i:j]])

                # Score this clip
                score = score_clip(clip_text, duration, segments[i:j])

                candidates.append({
                    'start': clip_start,
                    'end': clip_end,
                    'duration': duration,
                    'text': clip_text,
                    'segments': segments[i:j],
                    'score': score
                })

        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)

        # Filter overlapping clips
        final_clips = filter_overlapping_clips(candidates, NUM_CLIPS)

        # Add clip_index
        for idx, clip in enumerate(final_clips):
            clip['clip_index'] = idx

        print(f"[Detect] Found {len(final_clips)} clips")

        return {
            'statusCode': 200,
            'session_id': session_id,
            's3_video_key': s3_video_key,
            'clips': final_clips,
            'video_info': video_info
        }

    except Exception as e:
        print(f"[Detect] Error: {str(e)}")
        raise Exception(f"Failed to detect clips: {str(e)}")


def score_clip(text, duration, segments):
    """Score a clip based on viral potential"""
    score = 0.0
    text_lower = text.lower()

    # 1. Keyword scoring
    keyword_count = sum(1 for keyword in VIRAL_KEYWORDS if keyword in text_lower)
    score += keyword_count * 10

    # 2. Questions
    score += text.count('?') * 5

    # 3. Duration score
    duration_diff = abs(duration - TARGET_CLIP_DURATION)
    score += max(0, 20 - duration_diff)

    # 4. Completeness
    if text.strip().endswith(('.', '!', '?')):
        score += 10

    # 5. Speaking pace
    words = text.split()
    words_per_second = len(words) / duration if duration > 0 else 0
    if 2 <= words_per_second <= 4:
        score += 10

    # 6. Enthusiasm
    score += text.count('!') * 3

    # 7. Content length
    score += min(len(words), 100) * 0.5

    # 8. Action words
    action_words = ['discover', 'learn', 'understand', 'realize',
                   'achieve', 'create', 'build', 'master', 'unlock']
    action_count = sum(1 for word in action_words if word in text_lower)
    score += action_count * 5

    # 9. Numbers
    number_count = len(re.findall(r'\b\d+\b', text))
    score += number_count * 3

    # 10. Sentences
    sentence_count = len(re.findall(r'[.!?]+', text))
    score += sentence_count * 2

    return score


def filter_overlapping_clips(candidates, num_clips):
    """Filter out overlapping clips"""
    selected = []

    for candidate in candidates:
        overlaps = False
        for selected_clip in selected:
            if clips_overlap(candidate, selected_clip):
                overlaps = True
                break

        if not overlaps:
            selected.append(candidate)

        if len(selected) >= num_clips:
            break

    return selected


def clips_overlap(clip1, clip2, threshold=0.3):
    """Check if two clips overlap significantly"""
    start1, end1 = clip1['start'], clip1['end']
    start2, end2 = clip2['start'], clip2['end']

    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    overlap_duration = max(0, overlap_end - overlap_start)

    clip1_duration = end1 - start1
    clip2_duration = end2 - start2

    overlap_ratio1 = overlap_duration / clip1_duration if clip1_duration > 0 else 0
    overlap_ratio2 = overlap_duration / clip2_duration if clip2_duration > 0 else 0

    return max(overlap_ratio1, overlap_ratio2) > threshold
