"""
Configuration Settings - Cloud Optimized
Customize the behavior of the Viral Clip Extractor for Oracle Cloud deployment
"""

# Whisper Model Configuration
# For Oracle Cloud Free Tier (4 CPU cores), 'base' or 'tiny' is recommended
# Options: 'tiny', 'base', 'small', 'medium', 'large'
WHISPER_MODEL = 'base'  # 'tiny' for faster processing on limited resources

# Clip Duration Settings (in seconds)
MIN_CLIP_DURATION = 15
MAX_CLIP_DURATION = 60
TARGET_CLIP_DURATION = 30

# Number of clips to generate per video
# Recommended: 1-3 for cloud to save processing time
DEFAULT_NUM_CLIPS = 1

# Subtitle Settings
ADD_SUBTITLES_BY_DEFAULT = True
SUBTITLE_STYLE = 'bold'  # Options: 'default', 'bold', 'modern'

# Directory Settings
DOWNLOAD_DIR = 'downloads'
OUTPUT_DIR = 'outputs'

# Cloud-specific settings
# Auto-cleanup downloaded videos after processing to save disk space
AUTO_CLEANUP_DOWNLOADS = True

# Keep only N most recent downloads
KEEP_RECENT_DOWNLOADS = 5

# Maximum video duration to process (in seconds)
# Set a limit to avoid exhausting cloud resources
MAX_VIDEO_DURATION = 3600  # 1 hour

# Viral Keywords
VIRAL_KEYWORDS = [
    # Discovery & Learning
    'secret', 'hack', 'tip', 'trick', 'learn', 'discover',
    'found', 'revealed', 'hidden', 'unknown',

    # Impact & Transformation
    'amazing', 'incredible', 'shocking', 'unbelievable',
    'changed', 'transform', 'powerful', 'genius',

    # Superlatives
    'best', 'worst', 'top', 'ultimate', 'perfect',
    'greatest', 'biggest', 'fastest', 'easiest',

    # Urgency & Exclusivity
    'never', 'always', 'nobody', 'everyone', 'must',
    'need', 'should', 'immediately', 'now',

    # Questions & Engagement
    'how to', 'why', 'what if', 'did you know',

    # Mistakes & Warnings
    'mistake', 'avoid', 'wrong', 'fail', 'danger',

    # Speed & Efficiency
    'simple', 'easy', 'quick', 'fast', 'instant',

    # Value & Results
    'free', 'proven', 'guaranteed', 'results', 'success',

    # Stories & Experiences
    'story', 'experience', 'journey', 'crazy', 'insane'
]

# Clip Scoring Weights
SCORING_WEIGHTS = {
    'keyword_match': 10,
    'question_mark': 5,
    'exclamation_mark': 3,
    'duration_match': 20,
    'completeness': 10,
    'speaking_pace': 10,
    'action_words': 5,
    'numbers': 3,
    'sentences': 2,
}

# Speaking Pace (words per second)
IDEAL_SPEAKING_PACE_MIN = 2.0
IDEAL_SPEAKING_PACE_MAX = 4.0

# Clip Overlap Threshold
CLIP_OVERLAP_THRESHOLD = 0.3

# Web Server Settings - Cloud optimized
WEB_HOST = '0.0.0.0'  # Listen on all interfaces
WEB_PORT = 5000
DEBUG_MODE = False  # Always False in production

# Number of worker processes for Gunicorn (cloud deployment)
GUNICORN_WORKERS = 2
GUNICORN_TIMEOUT = 1800  # 30 minutes for long video processing

# Processing Options - Cloud optimized
# Delete original downloaded video after processing (RECOMMENDED for cloud)
DELETE_ORIGINAL_VIDEO = True

# Delete intermediate clips (clips without subtitles)
DELETE_INTERMEDIATE_CLIPS = True

# Save transcription files
SAVE_TRANSCRIPTION_JSON = True
SAVE_TRANSCRIPTION_SRT = False  # Disable to save space

# FFmpeg Options - Cloud optimized
# Use faster presets to reduce CPU usage
FFMPEG_PRESET = 'faster'  # Options: 'ultrafast', 'faster', 'fast', 'medium'
FFMPEG_CRF = 23  # Quality (18-28, lower = better quality but larger file)

# Advanced: Thread Settings
# Number of concurrent clip processing operations
# Set to 1 for sequential processing (more stable and less resource intensive)
MAX_CONCURRENT_CLIPS = 1

# Logging Configuration
LOG_LEVEL = 'INFO'  # Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
LOG_FILE = 'opus-clip.log'
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 3  # Keep 3 old log files

# Rate Limiting (optional - to prevent abuse on public cloud deployment)
ENABLE_RATE_LIMITING = False
MAX_REQUESTS_PER_HOUR = 10

# Resource Monitoring
ENABLE_RESOURCE_MONITORING = True
MAX_MEMORY_USAGE_MB = 20000  # 20 GB (leave 4 GB free on 24 GB system)
MAX_DISK_USAGE_PERCENT = 90
