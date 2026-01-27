#!/usr/bin/env python3
"""
LTX-2 Serverless API Client
Test script for the v18 URL-based API

Usage:
    python test_api_client.py --image-url URL --audio-url URL [--api-key KEY]

API Endpoint: https://api.runpod.ai/v2/42qdgmzjc9ldy5/runsync
"""
import argparse
import requests
import json
import base64
import time
import os
from pathlib import Path


# Configuration
ENDPOINT_ID = "42qdgmzjc9ldy5"
RUNPOD_API_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"


def run_sync(api_key: str, image_url: str, audio_url: str,
             prompt_positive: str = None, prompt_negative: str = None,
             quality_preset: str = "high", seed: int = None,
             width: int = 1280, height: int = 736) -> dict:
    """
    Run synchronous video generation.

    Args:
        api_key: RunPod API key
        image_url: URL to input image
        audio_url: URL to input audio
        prompt_positive: Positive prompt (optional)
        prompt_negative: Negative prompt (optional)
        quality_preset: "fast", "high", or "ultra" (default: high)
        seed: Random seed (optional, random if not provided)
        width: Video width (default: 1280)
        height: Video height (default: 736)

    Returns:
        API response dict
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "input": {
            "image_url": image_url,
            "audio_url": audio_url,
            "width": width,
            "height": height,
            "quality_preset": quality_preset
        }
    }

    if prompt_positive:
        payload["input"]["prompt_positive"] = prompt_positive
    if prompt_negative:
        payload["input"]["prompt_negative"] = prompt_negative
    if seed is not None:
        payload["input"]["seed"] = seed

    print(f"Sending request to {RUNPOD_API_URL}/runsync...")
    print(f"  Image URL: {image_url[:60]}...")
    print(f"  Audio URL: {audio_url[:60]}...")
    print(f"  Quality: {quality_preset}")
    print(f"  Resolution: {width}x{height}")

    start_time = time.time()

    response = requests.post(
        f"{RUNPOD_API_URL}/runsync",
        headers=headers,
        json=payload,
        timeout=660  # 11 minutes (generation can take up to 10 min)
    )

    elapsed = time.time() - start_time

    if response.status_code != 200:
        print(f"ERROR: HTTP {response.status_code}")
        print(response.text)
        return {"error": response.text}

    result = response.json()
    print(f"\nResponse received in {elapsed:.1f}s")

    return result


def run_async(api_key: str, image_url: str, audio_url: str,
              quality_preset: str = "high") -> str:
    """
    Run asynchronous video generation.

    Returns:
        Job ID
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "input": {
            "image_url": image_url,
            "audio_url": audio_url,
            "quality_preset": quality_preset
        }
    }

    response = requests.post(
        f"{RUNPOD_API_URL}/run",
        headers=headers,
        json=payload,
        timeout=30
    )

    result = response.json()
    job_id = result.get("id")
    print(f"Job submitted: {job_id}")
    return job_id


def check_status(api_key: str, job_id: str) -> dict:
    """Check status of async job."""
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(
        f"{RUNPOD_API_URL}/status/{job_id}",
        headers=headers,
        timeout=30
    )

    return response.json()


def save_video(result: dict, output_path: str = None) -> str:
    """
    Save video from API result.

    Args:
        result: API response containing video_base64
        output_path: Output file path (optional)

    Returns:
        Path to saved video
    """
    output = result.get("output", {})
    video_base64 = output.get("video_base64")

    if not video_base64:
        print("No video data in response")
        return None

    if output_path is None:
        timestamp = int(time.time())
        filename = output.get("video_filename", f"ltx2_output_{timestamp}.mp4")
        output_path = f"./{filename}"

    video_bytes = base64.b64decode(video_base64)

    with open(output_path, "wb") as f:
        f.write(video_bytes)

    file_size = len(video_bytes) / (1024 * 1024)
    print(f"Video saved: {output_path} ({file_size:.2f} MB)")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="LTX-2 Serverless API Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python test_api_client.py --image-url https://example.com/face.jpg --audio-url https://example.com/speech.mp3

  # With quality preset
  python test_api_client.py --image-url URL --audio-url URL --quality ultra

  # With custom prompt
  python test_api_client.py --image-url URL --audio-url URL --prompt "A person speaking confidently"

Quality Presets:
  fast  - Quick preview (~30-40s)
  high  - Production quality (~40-50s) [default]
  ultra - Maximum quality (~60-70s)
        """
    )

    parser.add_argument("--image-url", required=True, help="URL to input image")
    parser.add_argument("--audio-url", required=True, help="URL to input audio")
    parser.add_argument("--api-key", default=os.environ.get("RUNPOD_API_KEY"),
                        help="RunPod API key (or set RUNPOD_API_KEY env var)")
    parser.add_argument("--quality", default="high", choices=["fast", "high", "ultra"],
                        help="Quality preset (default: high)")
    parser.add_argument("--prompt", help="Positive prompt")
    parser.add_argument("--negative-prompt", help="Negative prompt")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--width", type=int, default=1280, help="Video width (default: 1280)")
    parser.add_argument("--height", type=int, default=736, help="Video height (default: 736)")
    parser.add_argument("--output", "-o", help="Output video path")
    parser.add_argument("--async", dest="async_mode", action="store_true",
                        help="Run in async mode (returns job ID)")

    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: API key required. Use --api-key or set RUNPOD_API_KEY env var")
        return 1

    print("=" * 60)
    print("LTX-2 Serverless API Client")
    print("=" * 60)

    if args.async_mode:
        # Async mode
        job_id = run_async(
            api_key=args.api_key,
            image_url=args.image_url,
            audio_url=args.audio_url,
            quality_preset=args.quality
        )
        print(f"\nTo check status:")
        print(f"  python test_api_client.py --check-status {job_id}")
    else:
        # Sync mode
        result = run_sync(
            api_key=args.api_key,
            image_url=args.image_url,
            audio_url=args.audio_url,
            prompt_positive=args.prompt,
            prompt_negative=args.negative_prompt,
            quality_preset=args.quality,
            seed=args.seed,
            width=args.width,
            height=args.height
        )

        # Print result summary
        if result.get("status") == "success":
            output = result.get("output", {})
            print("\n" + "=" * 60)
            print("Generation Successful!")
            print("=" * 60)
            print(f"  Resolution: {output.get('resolution')}")
            print(f"  Duration: {output.get('duration')}")
            print(f"  Frames: {output.get('frames')} @ {output.get('fps')} fps")
            print(f"  Quality: {output.get('quality_preset')}")
            print(f"  Seed: {output.get('seed')}")
            print(f"  Generation Time: {output.get('generation_time')}s")

            # Save video
            video_path = save_video(result, args.output)
            if video_path:
                print(f"\nVideo saved to: {video_path}")

        elif result.get("status") == "error":
            print("\n" + "=" * 60)
            print("Generation Failed!")
            print("=" * 60)
            print(f"  Error: {result.get('error')}")
            if result.get("traceback"):
                print(f"\nTraceback:\n{result.get('traceback')}")
            return 1
        else:
            print("\nUnexpected response:")
            print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    exit(main())
