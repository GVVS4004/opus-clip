"""
Enhanced Video Processing Module
- Karaoke-style word-by-word subtitle highlighting
- 9:16 vertical video conversion (TikTok/Instagram Reels format)
- Professional Opus Clip style output
"""
import os
import subprocess
from typing import List, Dict
import json


class VideoProcessorV2:
    def __init__(self, output_dir='outputs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def extract_clip_with_aspect_ratio(self, video_path: str, start_time: float, end_time: float,
                                      output_path: str, aspect_ratio: str = '9:16') -> str:
        """
        Extract a clip from video and convert to specified aspect ratio

        Args:
            video_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Path for output clip
            aspect_ratio: Target aspect ratio ('9:16', '16:9', '1:1', '4:5')

        Returns:
            Path to extracted clip
        """
        duration = end_time - start_time

        # Define aspect ratio specifications
        aspect_specs = {
            '9:16': {'width': 1080, 'height': 1920, 'description': 'Vertical (TikTok/Reels)'},
            '16:9': {'width': 1920, 'height': 1080, 'description': 'Horizontal (YouTube)'},
            '1:1': {'width': 1080, 'height': 1080, 'description': 'Square (Instagram)'},
            '4:5': {'width': 1080, 'height': 1350, 'description': 'Portrait (Instagram Feed)'}
        }

        if aspect_ratio not in aspect_specs:
            raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}. Supported: {list(aspect_specs.keys())}")

        spec = aspect_specs[aspect_ratio]
        target_width = spec['width']
        target_height = spec['height']

        # FFmpeg command to extract and convert to specified aspect ratio
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', video_path,
            '-t', str(duration),
            # Video processing: scale to target height, then crop to target width
            f'-vf', f'scale=-2:{target_height},crop={target_width}:{target_height}:(iw-{target_width})/2:0',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-avoid_negative_ts', 'make_zero',
            '-y',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to extract clip: {e.stderr.decode()}")

    def extract_clip_vertical(self, video_path: str, start_time: float, end_time: float,
                             output_path: str) -> str:
        """
        Extract a clip from video and convert to 9:16 vertical format (legacy method)

        Args:
            video_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Path for output clip

        Returns:
            Path to extracted clip
        """
        return self.extract_clip_with_aspect_ratio(video_path, start_time, end_time, output_path, '9:16')

    def add_karaoke_subtitles(self, video_path: str, clip_segments: List[Dict],
                              clip_start: float, output_path: str) -> str:
        """
        Add karaoke-style word-by-word highlighting subtitles

        Args:
            video_path: Path to video clip
            clip_segments: Transcription segments with word-level timestamps
            clip_start: Start time of clip in original video
            output_path: Path for output video with subtitles

        Returns:
            Path to video with karaoke subtitles
        """
        # Create ASS subtitle file with karaoke effects
        ass_path = video_path.replace('.mp4', '.ass')
        self._create_karaoke_ass(clip_segments, clip_start, ass_path)

        # Get video path for FFmpeg (fix Windows paths)
        ass_path_ffmpeg = ass_path.replace('\\', '/').replace(':', '\\:')

        # FFmpeg command to add subtitles
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f"ass={ass_path_ffmpeg}",
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            # Clean up temporary ASS file
            if os.path.exists(ass_path):
                os.remove(ass_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to add subtitles: {e.stderr.decode()}")

    def _create_karaoke_ass(self, segments: List[Dict], clip_start: float, output_path: str):
        """
        Create ASS subtitle file with karaoke word-by-word highlighting

        Args:
            segments: Transcription segments with word-level timestamps
            clip_start: Start time of clip in original video
            output_path: Path to save ASS file
        """
        # ASS file header with styling - Enhanced for visible highlighting
        ass_content = """[Script Info]
Title: Karaoke Subtitles with Highlighting
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,80,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,0,2,10,10,640,1
Style: Highlight,Arial,80,&H00000000,&H000000FF,&H00000000,&H00FFFF00,-1,0,0,0,100,100,0,0,3,4,3,2,10,10,640,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []

        for segment in segments:
            words = segment.get('words', [])

            if not words:
                # Fallback if no word-level timestamps
                start = max(0, segment['start'] - clip_start)
                end = max(0, segment['end'] - clip_start)
                start_time = self._format_ass_time(start)
                end_time = self._format_ass_time(end)
                text = segment['text'].strip()
                events.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")
            else:
                # Create karaoke effect with word-level highlighting
                # Show each word with bright highlight background when spoken
                words_per_line = 3  # Fewer words per line for better visibility

                for i in range(0, len(words), words_per_line):
                    line_words = words[i:i+words_per_line]

                    if not line_words:
                        continue

                    # Get timing for this line
                    line_start = max(0, line_words[0]['start'] - clip_start)
                    line_end = max(0, line_words[-1]['end'] - clip_start)

                    # Create effect: show all words in line, highlight current word
                    for active_idx, active_word in enumerate(line_words):
                        word_start = max(0, active_word['start'] - clip_start)
                        word_end = max(0, active_word['end'] - clip_start)

                        # Build the line with the active word highlighted
                        line_text = ""
                        for idx, word in enumerate(line_words):
                            word_text = word['word'].strip()

                            if idx == active_idx:
                                # This word is active - bright green, larger size, bold
                                # \fs95 = larger font size (popped up effect)
                                # \b1 = bold
                                # \c&H00FF00& = bright lime green color
                                # \3c&H000000& = black outline
                                line_text += f"{{\\fs95\\b1\\c&H00FF00&\\3c&H000000&\\bord3\\shad2}}{word_text}{{\\r}} "
                            else:
                                # Other words - white text, normal size
                                line_text += f"{{\\c&HFFFFFF&\\3c&H000000&\\bord3\\shad0}}{word_text}{{\\r}} "

                        start_time = self._format_ass_time(word_start)
                        end_time = self._format_ass_time(word_end)

                        # Add dialogue event for this moment
                        events.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line_text.strip()}")

        # Write ASS file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
            f.write('\n'.join(events))

    def _format_ass_time(self, seconds: float) -> str:
        """
        Format seconds to ASS timestamp format (H:MM:SS.cc)

        Args:
            seconds: Time in seconds

        Returns:
            Formatted ASS timestamp
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)

        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    def process_clip(self, video_path: str, clip_info: Dict, clip_number: int,
                     add_subtitles: bool = True, vertical: bool = True, aspect_ratio: str = '9:16') -> str:
        """
        Complete processing of a single clip with specified aspect ratio and karaoke subs

        Args:
            video_path: Path to source video
            clip_info: Clip information dict
            clip_number: Clip number for naming
            add_subtitles: Whether to add subtitles
            vertical: Whether to convert to 9:16 vertical format (legacy, use aspect_ratio instead)
            aspect_ratio: Target aspect ratio ('9:16', '16:9', '1:1', '4:5')

        Returns:
            Path to final processed clip
        """
        # Step 1: Extract clip with specified aspect ratio
        clip_filename = f"clip_{clip_number}_temp.mp4"
        clip_path = os.path.join(self.output_dir, clip_filename)

        print(f"Extracting clip {clip_number} ({aspect_ratio} format)...")

        # Use aspect_ratio parameter if provided, otherwise fall back to vertical flag
        if aspect_ratio != '9:16' or not vertical:
            if aspect_ratio == '16:9' or (not vertical and aspect_ratio == '9:16'):
                # Horizontal/original aspect ratio
                self.extract_clip_horizontal(
                    video_path,
                    clip_info['start'],
                    clip_info['end'],
                    clip_path
                )
            else:
                # Use specified aspect ratio
                self.extract_clip_with_aspect_ratio(
                    video_path,
                    clip_info['start'],
                    clip_info['end'],
                    clip_path,
                    aspect_ratio
                )
        else:
            # Default to 9:16 vertical
            self.extract_clip_with_aspect_ratio(
                video_path,
                clip_info['start'],
                clip_info['end'],
                clip_path,
                aspect_ratio
            )

        # Step 2: Add karaoke subtitles if requested
        if add_subtitles:
            print(f"Adding karaoke subtitles to clip {clip_number}...")
            final_filename = f"clip_{clip_number}_final.mp4"
            final_path = os.path.join(self.output_dir, final_filename)

            self.add_karaoke_subtitles(
                clip_path,
                clip_info['segments'],
                clip_info['start'],
                final_path
            )

            # Remove intermediate clip
            if os.path.exists(clip_path):
                os.remove(clip_path)

            return final_path
        else:
            # Rename temp to final
            final_filename = f"clip_{clip_number}_final.mp4"
            final_path = os.path.join(self.output_dir, final_filename)
            os.rename(clip_path, final_path)
            return final_path

    def extract_clip_horizontal(self, video_path: str, start_time: float, end_time: float,
                                output_path: str) -> str:
        """
        Extract clip maintaining original aspect ratio (16:9)

        Args:
            video_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Path for output clip

        Returns:
            Path to extracted clip
        """
        duration = end_time - start_time

        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', video_path,
            '-t', str(duration),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-avoid_negative_ts', 'make_zero',
            '-y',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to extract clip: {e.stderr.decode()}")


if __name__ == '__main__':
    # Test the processor
    processor = VideoProcessorV2()
    print("Video Processor V2 - Karaoke Subtitles + 9:16 Vertical Format")
    print("Ready to process clips!")
