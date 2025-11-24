"""
Flask Web Application - Cloud Optimized
Simple web interface for viral clip extraction with cloud-specific optimizations
"""
from flask import Flask, render_template, request, jsonify, send_file
import os
import threading
import logging
from pipeline_cloud import ViralClipPipelineCloud
from config_cloud import *

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max request size

# Store processing status
processing_status = {}

# Thread lock for status updates
status_lock = threading.Lock()


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_video():
    """Process a YouTube video"""
    try:
        data = request.json
        youtube_url = data.get('url', '').strip()

        if not youtube_url:
            return jsonify({'error': 'No URL provided'}), 400

        # Validate URL format
        if not ('youtube.com' in youtube_url or 'youtu.be' in youtube_url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        # Configuration from request or defaults
        config = {
            'whisper_model': data.get('model', WHISPER_MODEL),
            'min_clip_duration': int(data.get('min_duration', MIN_CLIP_DURATION)),
            'max_clip_duration': int(data.get('max_duration', MAX_CLIP_DURATION)),
            'num_clips': int(data.get('num_clips', DEFAULT_NUM_CLIPS)),
            'add_subtitles': data.get('add_subtitles', ADD_SUBTITLES_BY_DEFAULT),
            'aspect_ratio': data.get('aspect_ratio', '9:16')
        }

        # Validate configuration
        if config['num_clips'] > 10:
            return jsonify({'error': 'Maximum 10 clips allowed'}), 400

        # Generate session ID
        from datetime import datetime
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Initialize status
        with status_lock:
            processing_status[session_id] = {
                'status': 'starting',
                'progress': 0,
                'message': 'Initializing...',
                'results': None,
                'error': None
            }

        # Start processing in background thread
        thread = threading.Thread(
            target=process_video_background,
            args=(session_id, youtube_url, config)
        )
        thread.daemon = True
        thread.start()

        logger.info(f"Started processing session {session_id} for URL: {youtube_url}")

        return jsonify({
            'session_id': session_id,
            'message': 'Processing started'
        })

    except Exception as e:
        logger.error(f"Error in process endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


def process_video_background(session_id, youtube_url, config):
    """Background processing function"""
    try:
        logger.info(f"[{session_id}] Background processing started")

        # Update status
        with status_lock:
            processing_status[session_id]['status'] = 'processing'
            processing_status[session_id]['progress'] = 10
            processing_status[session_id]['message'] = 'Downloading video...'

        # Initialize pipeline
        pipeline = ViralClipPipelineCloud(
            whisper_model=config['whisper_model'],
            min_clip_duration=config['min_clip_duration'],
            max_clip_duration=config['max_clip_duration'],
            num_clips=config['num_clips']
        )

        # Update progress
        with status_lock:
            processing_status[session_id]['progress'] = 30
            processing_status[session_id]['message'] = 'Transcribing audio...'

        # Process video with auto-cleanup enabled
        results = pipeline.process_video(
            youtube_url,
            add_subtitles=config['add_subtitles'],
            cleanup_downloads=AUTO_CLEANUP_DOWNLOADS,
            aspect_ratio=config['aspect_ratio']
        )

        # Update status
        with status_lock:
            processing_status[session_id]['status'] = 'completed'
            processing_status[session_id]['progress'] = 100
            processing_status[session_id]['message'] = 'Processing complete!'
            processing_status[session_id]['results'] = results

        logger.info(f"[{session_id}] Processing completed successfully")

    except Exception as e:
        logger.error(f"[{session_id}] Processing failed: {str(e)}", exc_info=True)

        with status_lock:
            processing_status[session_id]['status'] = 'error'
            processing_status[session_id]['error'] = str(e)
            processing_status[session_id]['message'] = f'Error: {str(e)}'


@app.route('/status/<session_id>')
def get_status(session_id):
    """Get processing status"""
    with status_lock:
        if session_id not in processing_status:
            return jsonify({'error': 'Session not found'}), 404

        return jsonify(processing_status[session_id])


@app.route('/download/<path:filename>')
def download_file(filename):
    """Download a generated clip"""
    # Security: validate filename to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return jsonify({'error': 'Invalid filename'}), 400

    file_path = os.path.join('outputs', filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(file_path, as_attachment=True)


@app.route('/results')
def results():
    """View all processing results"""
    results_dir = 'outputs'
    if not os.path.exists(results_dir):
        return jsonify({'results': []})

    # Get all result files
    result_files = [f for f in os.listdir(results_dir) if f.startswith('results_') and f.endswith('.json')]

    results = []
    for filename in sorted(result_files, reverse=True)[:20]:  # Return only 20 most recent
        filepath = os.path.join(results_dir, filename)
        try:
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results.append(data)
        except Exception as e:
            logger.warning(f"Could not load result file {filename}: {str(e)}")

    return jsonify({'results': results})


@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    import psutil

    health_data = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
    }

    # Add resource usage if monitoring is enabled
    if ENABLE_RESOURCE_MONITORING:
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            health_data['resources'] = {
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024)
            }

            # Check if resources are critically low
            if memory.percent > 95 or disk.percent > MAX_DISK_USAGE_PERCENT:
                health_data['status'] = 'warning'
                health_data['message'] = 'Resources running low'

        except Exception as e:
            logger.warning(f"Could not get resource info: {str(e)}")

    return jsonify(health_data)


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('downloads', exist_ok=True)
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    logger.info("=" * 60)
    logger.info("VIRAL CLIP EXTRACTOR - Web Interface (Cloud Edition)")
    logger.info("=" * 60)
    logger.info("Starting server...")
    logger.info(f"Listening on: http://{WEB_HOST}:{WEB_PORT}")
    logger.info("Press CTRL+C to stop the server")
    logger.info("=" * 60)

    # Run server
    # For production: use Gunicorn instead
    # gunicorn -w 2 -b 0.0.0.0:5000 --timeout 1800 app_cloud:app
    app.run(debug=DEBUG_MODE, host=WEB_HOST, port=WEB_PORT, threaded=True)
