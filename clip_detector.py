"""
Viral Clip Detection Module
Identifies potential viral short clips from long-form content
"""
import re
from typing import List, Dict, Tuple
import numpy as np


class ClipDetector:
    def __init__(self,
                 min_clip_duration=15,
                 max_clip_duration=60,
                 target_clip_duration=30):
        """
        Initialize clip detector

        Args:
            min_clip_duration: Minimum clip length in seconds
            max_clip_duration: Maximum clip length in seconds
            target_clip_duration: Target clip length in seconds
        """
        self.min_duration = min_clip_duration
        self.max_duration = max_clip_duration
        self.target_duration = target_clip_duration

        # Keywords that indicate engaging content
        self.viral_keywords = [
            'secret', 'hack', 'tip', 'trick', 'amazing', 'incredible',
            'shocking', 'revealed', 'how to', 'why', 'never', 'always',
            'mistake', 'avoid', 'best', 'worst', 'truth', 'nobody',
            'everyone', 'simple', 'easy', 'quick', 'fast', 'powerful',
            'changed', 'transform', 'learn', 'discover', 'found',
            'story', 'crazy', 'insane', 'genius', 'strategy'
        ]

    def detect_clips(self, segments: List[Dict], num_clips: int = 5) -> List[Dict]:
        """
        Detect potential viral clips from transcription segments

        Args:
            segments: List of transcription segments with timestamps
            num_clips: Number of top clips to return

        Returns:
            List of clip candidates with scores
        """
        candidates = []

        # Create sliding windows of segments that fit duration constraints
        for i in range(len(segments)):
            for j in range(i + 1, len(segments) + 1):
                clip_start = segments[i]['start']
                clip_end = segments[j - 1]['end']
                duration = clip_end - clip_start

                # Check duration constraints
                if duration < self.min_duration:
                    continue
                if duration > self.max_duration:
                    break

                # Extract text for this clip
                clip_text = ' '.join([seg['text'] for seg in segments[i:j]])

                # Score this clip candidate
                score = self._score_clip(
                    clip_text,
                    duration,
                    segments[i:j]
                )

                candidates.append({
                    'start': clip_start,
                    'end': clip_end,
                    'duration': duration,
                    'text': clip_text,
                    'segments': segments[i:j],
                    'score': score
                })

        # Sort by score and return top candidates
        candidates.sort(key=lambda x: x['score'], reverse=True)

        # Filter overlapping clips - keep highest scored non-overlapping clips
        final_clips = self._filter_overlapping_clips(candidates, num_clips)

        return final_clips[:num_clips]

    def _score_clip(self, text: str, duration: float, segments: List[Dict]) -> float:
        """
        Score a clip candidate based on various factors

        Args:
            text: Clip text content
            duration: Clip duration in seconds
            segments: Clip segments

        Returns:
            Clip score (higher is better)
        """
        score = 0.0
        text_lower = text.lower()

        # 1. Keyword scoring - check for viral keywords
        keyword_count = sum(1 for keyword in self.viral_keywords if keyword in text_lower)
        score += keyword_count * 10

        # 2. Question presence (questions are engaging)
        question_count = text.count('?')
        score += question_count * 5

        # 3. Duration score - prefer clips closer to target duration
        duration_diff = abs(duration - self.target_duration)
        duration_score = max(0, 20 - duration_diff)
        score += duration_score

        # 4. Completeness - prefer clips that end with sentence endings
        if text.strip().endswith(('.', '!', '?')):
            score += 10

        # 5. Word count density (avoid too sparse or too dense content)
        words = text.split()
        words_per_second = len(words) / duration if duration > 0 else 0
        if 2 <= words_per_second <= 4:  # Good speaking pace
            score += 10

        # 6. Exclamation marks (enthusiasm)
        score += text.count('!') * 3

        # 7. Length of text (more content is generally better)
        score += min(len(words), 100) * 0.5

        # 8. Action words and power verbs
        action_words = ['discover', 'learn', 'understand', 'realize',
                       'achieve', 'create', 'build', 'master', 'unlock']
        action_count = sum(1 for word in action_words if word in text_lower)
        score += action_count * 5

        # 9. Numbers (lists and data are engaging)
        number_count = len(re.findall(r'\b\d+\b', text))
        score += number_count * 3

        # 10. Sentence count (multiple complete thoughts)
        sentence_count = len(re.findall(r'[.!?]+', text))
        score += sentence_count * 2

        return score

    def _filter_overlapping_clips(self, candidates: List[Dict], num_clips: int) -> List[Dict]:
        """
        Filter out overlapping clips, keeping highest scored ones

        Args:
            candidates: Sorted list of clip candidates
            num_clips: Target number of clips

        Returns:
            List of non-overlapping clips
        """
        selected = []

        for candidate in candidates:
            # Check if this candidate overlaps with any selected clip
            overlaps = False
            for selected_clip in selected:
                if self._clips_overlap(candidate, selected_clip):
                    overlaps = True
                    break

            if not overlaps:
                selected.append(candidate)

            if len(selected) >= num_clips * 2:  # Get extra candidates
                break

        return selected

    def _clips_overlap(self, clip1: Dict, clip2: Dict, threshold: float = 0.3) -> bool:
        """
        Check if two clips overlap significantly

        Args:
            clip1: First clip
            clip2: Second clip
            threshold: Overlap threshold (0.3 = 30% overlap)

        Returns:
            True if clips overlap significantly
        """
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


if __name__ == '__main__':
    # Test with sample segments
    sample_segments = [
        {'start': 0, 'end': 5, 'text': 'Hello everyone, welcome to this video.'},
        {'start': 5, 'end': 12, 'text': 'Today I want to share an amazing secret that changed my life.'},
        {'start': 12, 'end': 20, 'text': 'This simple trick will help you learn anything 10x faster.'},
        {'start': 20, 'end': 28, 'text': 'First, you need to understand the basics.'},
        {'start': 28, 'end': 35, 'text': 'Let me show you how to do this step by step.'},
    ]

    detector = ClipDetector()
    clips = detector.detect_clips(sample_segments, num_clips=2)

    print("Detected Clips:")
    for i, clip in enumerate(clips, 1):
        print(f"\nClip {i}:")
        print(f"Time: {clip['start']:.1f}s - {clip['end']:.1f}s")
        print(f"Duration: {clip['duration']:.1f}s")
        print(f"Score: {clip['score']:.1f}")
        print(f"Text: {clip['text']}")
