"""
Main Processing Pipeline - Cloud Optimized
Orchestrates all components with memory optimization and cloud-specific error handling
"""
import os
import json
import logging
from datetime import datetime
from downloader_cloud import VideoDownloaderCloud
from transcriber import AudioTranscriber
from clip_detector import ClipDetector
from video_processor_v2 import VideoProcessorV2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ViralClipPipelineCloud:
    def __init__(self,
                 whisper_model='base',
                 min_clip_duration=15,
                 max_clip_duration=60,
                 num_clips=1):
        """
        Initialize the viral clip extraction pipeline - Cloud optimized

        Args:
            whisper_model: Whisper model size ('tiny', 'base', 'small', 'medium')
            min_clip_duration: Minimum clip length in seconds
            max_clip_duration: Maximum clip length in seconds
            num_clips: Number of clips to generate
        """
        self.downloader = VideoDownloaderCloud()
        self.transcriber = AudioTranscriber(model_size=whisper_model)
        self.clip_detector = ClipDetector(
            min_clip_duration=min_clip_duration,
            max_clip_duration=max_clip_duration
        )
        self.video_processor = VideoProcessorV2()
        self.num_clips = num_clips

    def process_video(self, youtube_url: str, add_subtitles: bool = True,
                     cleanup_downloads: bool = True, aspect_ratio: str = '9:16') -> dict:
        """
        Process a YouTube video to extract viral clips - Cloud optimized

        Args:
            youtube_url: YouTube video URL
            add_subtitles: Whether to add subtitles to clips
            cleanup_downloads: Whether to clean up downloaded files after processing
            aspect_ratio: Target aspect ratio ('9:16', '16:9', '1:1', '4:5')

        Returns:
            dict: Processing results with clip paths and metadata
        """
        logger.info("=" * 60)
        logger.info("VIRAL CLIP EXTRACTOR - Processing Pipeline (Cloud)")
        logger.info("=" * 60)

        # Create unique session ID
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = None

        try:
            # Step 1: Download video
            logger.info("[1/5] Downloading video from YouTube...")
            video_filename = f"video_{session_id}"
            video_path, video_info = self.downloader.download_video(
                youtube_url,
                output_filename=video_filename
            )
            logger.info(f"✓ Downloaded: {video_info.get('title', 'Unknown')}")
            logger.info(f"  Duration: {video_info.get('duration', 0)} seconds")

            # Step 2: Transcribe audio
            logger.info("[2/5] Transcribing audio with Whisper AI...")
            transcription = self.transcriber.transcribe(video_path)
            segments = self.transcriber.get_segments_with_timestamps(transcription)
            logger.info(f"✓ Transcribed {len(segments)} segments")

            # Save transcription
            transcription_path = video_path.replace('.mp4', '_transcription.json')
            self.transcriber.save_transcription(transcription, transcription_path)
            logger.info(f"  Transcription saved to: {transcription_path}")

            # Step 3: Detect viral clips
            logger.info("[3/5] Detecting viral clip candidates...")
            clip_candidates = self.clip_detector.detect_clips(
                segments,
                num_clips=self.num_clips
            )
            logger.info(f"✓ Detected {len(clip_candidates)} potential viral clips")

            # Display clip info
            for i, clip in enumerate(clip_candidates, 1):
                logger.info(f"  Clip {i}:")
                logger.info(f"    Time: {clip['start']:.1f}s - {clip['end']:.1f}s")
                logger.info(f"    Duration: {clip['duration']:.1f}s")
                logger.info(f"    Score: {clip['score']:.1f}")
                logger.info(f"    Preview: {clip['text'][:100]}...")

            # Step 4: Process clips
            logger.info("[4/5] Extracting and processing clips...")
            processed_clips = []

            for i, clip_info in enumerate(clip_candidates, 1):
                try:
                    clip_path = self.video_processor.process_clip(
                        video_path,
                        clip_info,
                        i,
                        add_subtitles=add_subtitles,
                        aspect_ratio=aspect_ratio  # User-selected aspect ratio
                    )

                    processed_clips.append({
                        'number': i,
                        'path': clip_path,
                        'start': clip_info['start'],
                        'end': clip_info['end'],
                        'duration': clip_info['duration'],
                        'text': clip_info['text'],
                        'score': clip_info['score']
                    })

                    logger.info(f"  ✓ Clip {i} created: {os.path.basename(clip_path)}")

                except Exception as e:
                    logger.error(f"  ✗ Failed to process clip {i}: {str(e)}")

            # Step 5: Save results
            logger.info("[5/5] Saving results...")
            results = {
                'session_id': session_id,
                'youtube_url': youtube_url,
                'video_title': video_info.get('title', 'Unknown'),
                'video_duration': video_info.get('duration', 0),
                'processed_at': datetime.now().isoformat(),
                'clips': processed_clips,
                'transcription_path': transcription_path
            }

            results_path = os.path.join('outputs', f'results_{session_id}.json')
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Results saved to: {results_path}")

            # Cloud optimization: Clean up downloads to save disk space
            if cleanup_downloads and video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    logger.info(f"✓ Cleaned up downloaded video: {video_path}")
                except Exception as e:
                    logger.warning(f"Could not clean up video file: {str(e)}")

            # Clean up old downloads (keep only 5 most recent)
            self.downloader.cleanup_downloads(keep_latest=5)

            # Summary
            logger.info("=" * 60)
            logger.info("PROCESSING COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"Generated {len(processed_clips)} viral clips")
            logger.info(f"Output directory: {os.path.abspath('outputs')}")
            logger.info("\nClip files:")
            for clip in processed_clips:
                logger.info(f"  - {os.path.basename(clip['path'])}")

            return results

        except Exception as e:
            logger.error(f"✗ Error during processing: {str(e)}", exc_info=True)

            # Clean up on error
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    logger.info(f"Cleaned up video file after error: {video_path}")
                except:
                    pass

            raise


def main():
    """
    Command-line interface for the pipeline
    """
    print("\n" + "=" * 60)
    print("VIRAL CLIP EXTRACTOR - Cloud Edition")
    print("Create viral short clips from YouTube videos")
    print("=" * 60 + "\n")

    # Get user input
    youtube_url = input("Enter YouTube URL: ").strip()

    if not youtube_url:
        print("Error: No URL provided")
        return

    # Configuration
    print("\nConfiguration:")
    print("  - Whisper Model: base (good balance of speed/accuracy)")
    print("  - Clip Duration: 15-60 seconds")
    print("  - Number of Clips: 1 (best clip only)")
    print("  - Subtitles: Enabled")
    print("  - Auto-cleanup: Enabled (saves disk space)")

    proceed = input("\nProceed with these settings? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Cancelled.")
        return

    # Initialize pipeline
    pipeline = ViralClipPipelineCloud(
        whisper_model='base',
        min_clip_duration=15,
        max_clip_duration=60,
        num_clips=1
    )

    # Process video
    try:
        results = pipeline.process_video(youtube_url, add_subtitles=True)
        print("\n✓ Success! Your viral clips are ready to upload.")

    except Exception as e:
        print(f"\n✗ Failed to process video: {str(e)}")


if __name__ == '__main__':
    main()
