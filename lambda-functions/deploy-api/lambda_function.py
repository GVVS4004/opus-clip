"""
Lambda Function 6: API Gateway Handler
Handles HTTP requests and starts Step Functions execution
"""
import json
import boto3
import uuid
import os

# Storage helper - works with S3, R2, B2, and any S3-compatible storage
def get_storage_client():
    """Get S3-compatible storage client (supports AWS S3, Cloudflare R2, Backblaze B2, etc.)"""
    endpoint = os.environ.get('R2_ENDPOINT') or os.environ.get('STORAGE_ENDPOINT')
    access_key = os.environ.get('R2_ACCESS_KEY') or os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('R2_SECRET_KEY') or os.environ.get('AWS_SECRET_ACCESS_KEY')

    if endpoint:
        print(f"[Storage] Using custom endpoint: {endpoint}")
        return boto3.client('s3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=os.environ.get('AWS_REGION', 'auto')
        )
    print("[Storage] Using AWS S3 (default)")
    return boto3.client('s3')

stepfunctions = boto3.client('stepfunctions')
s3 = get_storage_client()

STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'opus-clip-videos')

def lambda_handler(event, context):
    """
    API Gateway Lambda handler

    Endpoints:
    - POST /process: Start video processing
    - GET /status/{session_id}: Get processing status
    - GET /result/{session_id}: Get final result
    """

    http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'GET'))
    path = event.get('path', event.get('rawPath', '/'))

    print(f"[API] Method: {http_method}, Path: {path}")

    # Route request
    if http_method == 'POST' and path == '/process':
        return handle_process(event)
    elif http_method == 'GET' and '/status/' in path:
        return handle_status(event, path)
    elif http_method == 'GET' and '/result/' in path:
        return handle_result(event, path)
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Not found'})
        }


def handle_process(event):
    """Handle POST /process - Start video processing"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        youtube_url = body.get('youtube_url')

        if not youtube_url:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'youtube_url is required'})
            }

        # Generate session ID
        session_id = str(uuid.uuid4())

        print(f"[API] Starting processing for session: {session_id}")
        print(f"[API] YouTube URL: {youtube_url}")

        # Start Step Functions execution
        execution = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=session_id.replace('-', '_'),  # Step Functions doesn't allow hyphens
            input=json.dumps({
                'session_id': session_id,
                'youtube_url': youtube_url
            })
        )

        return {
            'statusCode': 202,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'session_id': session_id,
                'status': 'processing',
                'execution_arn': execution['executionArn']
            })
        }

    except Exception as e:
        print(f"[API] Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }


def handle_status(event, path):
    """Handle GET /status/{session_id} - Get processing status"""
    try:
        # Extract session ID from path
        session_id = path.split('/status/')[-1]
        execution_name = session_id.replace('-', '_')

        print(f"[API] Getting status for session: {session_id}")

        # Get execution status
        try:
            response = stepfunctions.describe_execution(
                executionArn=f"{STATE_MACHINE_ARN.replace(':stateMachine:', ':execution:')}:{execution_name}"
            )

            status_map = {
                'RUNNING': 'processing',
                'SUCCEEDED': 'completed',
                'FAILED': 'failed',
                'TIMED_OUT': 'failed',
                'ABORTED': 'failed'
            }

            result = {
                'session_id': session_id,
                'status': status_map.get(response['status'], 'unknown'),
                'start_time': response['startDate'].isoformat()
            }

            # If completed, include output
            if response['status'] == 'SUCCEEDED':
                output = json.loads(response.get('output', '{}'))
                result['result'] = output

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }

        except stepfunctions.exceptions.ExecutionDoesNotExist:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Session not found'})
            }

    except Exception as e:
        print(f"[API] Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }


def handle_result(event, path):
    """Handle GET /result/{session_id} - Get final result from S3"""
    try:
        # Extract session ID from path
        session_id = path.split('/result/')[-1]

        print(f"[API] Getting result for session: {session_id}")

        # Get result from S3
        result_key = f"{session_id}/result.json"
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=result_key)
        result = json.loads(obj['Body'].read())

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }

    except s3.exceptions.NoSuchKey:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Result not found'})
        }
    except Exception as e:
        print(f"[API] Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
