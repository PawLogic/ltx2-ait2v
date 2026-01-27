#!/usr/bin/env python3
"""
URL downloader with validation for images and audio.
Extracts audio duration using librosa.
"""
import os
import io
import requests
from typing import Tuple
from urllib.parse import urlparse


class URLDownloader:
    """Download images and audio from URLs with validation."""

    ALLOWED_IMAGE_TYPES = {
        'image/jpeg', 'image/png', 'image/webp', 'image/jpg',
        'application/octet-stream'  # Some servers don't set proper content-type
    }
    ALLOWED_AUDIO_TYPES = {
        'audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/x-wav',
        'audio/x-m4a', 'audio/mp4', 'audio/aac',
        'application/octet-stream'  # Some servers don't set proper content-type
    }
    MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
    MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100MB

    @staticmethod
    def download_image(url: str) -> Tuple[bytes, str]:
        """
        Download image from URL with validation.

        Args:
            url: Image URL to download

        Returns:
            Tuple of (image_bytes, filename)

        Raises:
            ValueError: If image type is invalid or file too large
            requests.RequestException: If download fails
        """
        print(f"  Downloading image from: {url[:80]}...")

        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()

        # Check content type (relaxed validation)
        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()

        # Get file extension from URL
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        filename = os.path.basename(path) or 'input.jpg'

        # Validate by extension if content-type is ambiguous
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        _, ext = os.path.splitext(filename)

        if content_type not in URLDownloader.ALLOWED_IMAGE_TYPES:
            if ext.lower() not in valid_extensions:
                raise ValueError(f"Invalid image type: {content_type}, extension: {ext}")

        # Check size
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > URLDownloader.MAX_IMAGE_SIZE:
            raise ValueError(f"Image too large: {int(content_length)} bytes (max {URLDownloader.MAX_IMAGE_SIZE})")

        # Download content
        image_bytes = response.content

        # Final size check
        if len(image_bytes) > URLDownloader.MAX_IMAGE_SIZE:
            raise ValueError(f"Image too large: {len(image_bytes)} bytes")

        # Ensure filename has extension
        if not ext:
            filename = 'input.jpg'

        print(f"  Downloaded image: {len(image_bytes)} bytes -> {filename}")
        return image_bytes, filename

    @staticmethod
    def download_audio(url: str) -> Tuple[bytes, str, float]:
        """
        Download audio from URL and extract duration.

        Args:
            url: Audio URL to download

        Returns:
            Tuple of (audio_bytes, filename, duration_seconds)

        Raises:
            ValueError: If audio type is invalid or file too large
            requests.RequestException: If download fails
        """
        print(f"  Downloading audio from: {url[:80]}...")

        response = requests.get(url, timeout=120, stream=True)
        response.raise_for_status()

        # Check content type (relaxed validation)
        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()

        # Get file extension from URL
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        filename = os.path.basename(path) or 'input.mp3'

        # Validate by extension if content-type is ambiguous
        valid_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.ogg'}
        _, ext = os.path.splitext(filename)

        if content_type not in URLDownloader.ALLOWED_AUDIO_TYPES:
            if ext.lower() not in valid_extensions:
                raise ValueError(f"Invalid audio type: {content_type}, extension: {ext}")

        # Check size
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > URLDownloader.MAX_AUDIO_SIZE:
            raise ValueError(f"Audio too large: {int(content_length)} bytes (max {URLDownloader.MAX_AUDIO_SIZE})")

        # Download content
        audio_bytes = response.content

        # Final size check
        if len(audio_bytes) > URLDownloader.MAX_AUDIO_SIZE:
            raise ValueError(f"Audio too large: {len(audio_bytes)} bytes")

        # Extract duration using librosa
        duration = URLDownloader._get_audio_duration(audio_bytes, filename)

        # Ensure filename has extension
        if not ext:
            filename = 'input.mp3'

        print(f"  Downloaded audio: {len(audio_bytes)} bytes, duration: {duration:.2f}s -> {filename}")
        return audio_bytes, filename, duration

    @staticmethod
    def _get_audio_duration(audio_bytes: bytes, filename: str = "audio.mp3") -> float:
        """
        Extract audio duration using librosa.

        Args:
            audio_bytes: Raw audio bytes
            filename: Original filename (for format detection)

        Returns:
            Duration in seconds
        """
        import librosa
        import tempfile
        import os

        # Write to temp file for librosa (more reliable than BytesIO for some formats)
        _, ext = os.path.splitext(filename)
        if not ext:
            ext = '.mp3'

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            duration = librosa.get_duration(path=tmp_path)
            return duration
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False
