#!/usr/bin/env python3
"""
GCS Uploader for LTX-2 Video Output

Uploads generated videos to Google Cloud Storage and returns public URLs.
"""
import os
import json
from datetime import datetime
from google.cloud import storage
from google.oauth2 import service_account

# Configuration
GCS_BUCKET = "dramaland-public"
GCS_BASE_PATH = "ugc_media"
SERVICE_ACCOUNT_PATH = "/workspace/gcs-credentials.json"

# Fallback paths for service account
SERVICE_ACCOUNT_PATHS = [
    "/workspace/gcs-credentials.json",
    "/gcs-credentials.json",
    "/workspace/handler/gcs-credentials.json",
]


def get_gcs_client():
    """
    Get authenticated GCS client.

    Returns:
        storage.Client: Authenticated GCS client

    Raises:
        FileNotFoundError: If service account credentials not found
    """
    # Try each possible path
    creds_path = None
    for path in SERVICE_ACCOUNT_PATHS:
        if os.path.exists(path):
            creds_path = path
            break

    if not creds_path:
        # Check environment variable
        env_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if env_creds and os.path.exists(env_creds):
            creds_path = env_creds

    if not creds_path:
        raise FileNotFoundError(
            f"GCS credentials not found. Tried: {SERVICE_ACCOUNT_PATHS}"
        )

    credentials = service_account.Credentials.from_service_account_file(creds_path)
    return storage.Client(credentials=credentials, project=credentials.project_id)


def upload_video_to_gcs(
    video_path: str,
    job_id: str = None,
    subfolder: str = "videos"
) -> dict:
    """
    Upload video to GCS and return URLs.

    Args:
        video_path: Local path to video file
        job_id: Optional job ID for organizing files (uses date path if not provided)
        subfolder: Subfolder name (default: "videos")

    Returns:
        dict with:
            - success: bool
            - gcs_url: gs:// URL
            - public_url: https:// URL
            - filename: uploaded filename
            - size_bytes: file size
            - error: error message if failed
    """
    try:
        if not os.path.exists(video_path):
            return {
                "success": False,
                "gcs_url": None,
                "public_url": None,
                "filename": None,
                "size_bytes": None,
                "error": f"Video file not found: {video_path}"
            }

        # Get file info
        file_size = os.path.getsize(video_path)
        original_filename = os.path.basename(video_path)

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Keep original extension
        name_part = os.path.splitext(original_filename)[0]
        ext = os.path.splitext(original_filename)[1] or ".mp4"
        unique_filename = f"{timestamp}_{name_part}{ext}"

        # Build GCS path
        if job_id:
            gcs_path = f"{GCS_BASE_PATH}/{job_id}/{subfolder}/{unique_filename}"
        else:
            # Use date-based path
            date_path = datetime.now().strftime("%Y/%m/%d")
            gcs_path = f"{GCS_BASE_PATH}/{date_path}/{subfolder}/{unique_filename}"

        # Upload to GCS
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(gcs_path)

        # Set content type
        blob.content_type = "video/mp4"

        # Upload with progress logging
        print(f"Uploading to GCS: {gcs_path} ({file_size / 1024 / 1024:.1f} MB)")
        blob.upload_from_filename(video_path)

        # Build URLs
        gcs_url = f"gs://{GCS_BUCKET}/{gcs_path}"
        public_url = f"https://storage.googleapis.com/{GCS_BUCKET}/{gcs_path}"

        print(f"Upload complete: {public_url}")

        return {
            "success": True,
            "gcs_url": gcs_url,
            "public_url": public_url,
            "filename": unique_filename,
            "size_bytes": file_size,
            "error": None
        }

    except FileNotFoundError as e:
        return {
            "success": False,
            "gcs_url": None,
            "public_url": None,
            "filename": None,
            "size_bytes": None,
            "error": f"GCS credentials error: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "gcs_url": None,
            "public_url": None,
            "filename": None,
            "size_bytes": None,
            "error": f"GCS upload failed: {e}"
        }


def delete_local_video(video_path: str) -> bool:
    """
    Delete local video file after successful upload.

    Args:
        video_path: Path to video file

    Returns:
        True if deleted, False otherwise
    """
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"Deleted local file: {video_path}")
            return True
    except Exception as e:
        print(f"Warning: Could not delete local file: {e}")
    return False
