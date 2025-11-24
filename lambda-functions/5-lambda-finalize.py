"""
Lambda Function 5: Finalize Processing
Aggregates results and generates pre-signed URLs
"""
import json
import boto3
import os

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'opus-clip-videos')

def lambda_handler(event, context):
    """
    Finalize processing and generate download URLs

    Input event:
    {
        "session_id": "uuid",
        "processed_clips": [
            {
                "clip_index": 0,
                "s3_clip_key": "session_id/clips/clip_0.mp4"
            },
            ...
        ],
        "video_info": {...}
    }

    Output:
    {
        "session_id": "uuid",
        "status": "completed",
        "clips": [
            {
                "clip_index": 0,
                "download_url": "https://...",
                "s3_key": "..."
            }
        ],
        "video_info": {...}
    }
    """
    try:
        session_id = event['session_id']
        processed_clips = event.get('processed_clips', [])
        video_info = event.get('video_info', {})

        print(f"[Finalize] Session: {session_id}")
        print(f"[Finalize] Processing {len(processed_clips)} clips")

        # Generate pre-signed URLs (valid for 24 hours)
        clip_urls = []
        for clip in processed_clips:
            s3_key = clip['s3_clip_key']

            # Generate pre-signed URL
            url = s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=86400  # 24 hours
            )

            clip_urls.append({
                'clip_index': clip['clip_index'],
                'download_url': url,
                's3_key': s3_key
            })

        # Sort by clip index
        clip_urls.sort(key=lambda x: x['clip_index'])

        result = {
            'session_id': session_id,
            'status': 'completed',
            'clips': clip_urls,
            'total_clips': len(clip_urls),
            'video_info': video_info
        }

        # Save result to S3
        result_key = f"{session_id}/result.json"
        print(f"[Finalize] Saving result to S3: {result_key}")

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=result_key,
            Body=json.dumps(result, indent=2),
            ContentType='application/json'
        )

        print(f"[Finalize] Complete! Generated {len(clip_urls)} download URLs")

        return {
            'statusCode': 200,
            **result
        }

    except Exception as e:
        print(f"[Finalize] Error: {str(e)}")
        raise Exception(f"Failed to finalize: {str(e)}")
