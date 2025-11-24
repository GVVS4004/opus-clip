"""
Audio Transcription Module
Uses OpenAI Whisper for accurate speech-to-text with timestamps
"""
import whisper
import os
import json
from typing import List, Dict


class AudioTranscriber:
    def __init__(self, model_size='base'):
        """
        Initialize Whisper model

        Args:
            model_size: 'tiny', 'base', 'small', 'medium', 'large'
                       (base is good balance of speed/accuracy)
        """
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        print("Model loaded successfully!")

    def transcribe(self, video_path: str) -> Dict:
        """
        Transcribe video/audio file

        Args:
            video_path: Path to video or audio file

        Returns:
            dict: Transcription with segments and timestamps
        """
        print(f"Transcribing {video_path}...")

        # Transcribe with word-level timestamps
        result = self.model.transcribe(
            video_path,
            word_timestamps=True,
            verbose=False
        )

        return result

    def get_segments_with_timestamps(self, transcription: Dict) -> List[Dict]:
        """
        Extract segments with start/end timestamps

        Args:
            transcription: Result from transcribe()

        Returns:
            List of segments with text and timestamps
        """
        segments = []

        for segment in transcription.get('segments', []):
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'words': segment.get('words', [])
            })

        return segments

    def save_transcription(self, transcription: Dict, output_path: str):
        """
        Save transcription to JSON file

        Args:
            transcription: Transcription result
            output_path: Path to save JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcription, f, indent=2, ensure_ascii=False)

    def generate_srt(self, transcription: Dict, output_path: str):
        """
        Generate SRT subtitle file from transcription

        Args:
            transcription: Transcription result
            output_path: Path to save SRT file
        """
        segments = self.get_segments_with_timestamps(transcription)

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                start_time = self._format_timestamp(segment['start'])
                end_time = self._format_timestamp(segment['end'])

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment['text']}\n")
                f.write("\n")

    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds to SRT timestamp format (HH:MM:SS,mmm)

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


if __name__ == '__main__':
    # Test the transcriber
    transcriber = AudioTranscriber(model_size='base')
    video_path = input("Enter video path: ")

    if os.path.exists(video_path):
        result = transcriber.transcribe(video_path)
        print("\nTranscription:")
        print(result['text'])

        # Save SRT
        srt_path = video_path.replace('.mp4', '.srt')
        transcriber.generate_srt(result, srt_path)
        print(f"\nSRT saved to: {srt_path}")
    else:
        print("File not found!")
