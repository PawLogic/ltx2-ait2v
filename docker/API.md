# LTX-2 Video Generation API

RunPod Serverless API for generating video with two modes:
- **Mode 1 (Lip-sync)**: Image + Audio → Video with lip synchronization
- **Mode 2 (Audio Gen)**: Image + Duration → Video + Generated audio

**Version**: v34

## Endpoint

| Environment | URL |
|-------------|-----|
| Production | `https://api.runpod.ai/v2/42qdgmzjc9ldy5` |

## Authentication

```
Authorization: Bearer {RUNPOD_API_KEY}
```

## API Calls

### Synchronous (Wait for result)

```
POST /runsync
```

Waits for video generation to complete (timeout: 10 minutes).

### Asynchronous (Immediate return)

```
POST /run          # Submit job
GET /status/{id}   # Check status
```

## Mode 1: Lip-sync (Image + Audio)

Generate video with lip synchronization to provided audio.

### Request Format

```json
{
  "input": {
    "image_url": "https://example.com/portrait.jpg",
    "audio_url": "https://example.com/speech.mp3",
    "prompt_positive": "A person speaks naturally with perfect lip synchronization",
    "quality_preset": "high",
    "lora_camera": 0.3
  }
}
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `image_url` | string | Yes | - | URL to portrait image (JPG/PNG) |
| `audio_url` | string | Yes | - | URL to audio file (MP3/WAV) |
| `prompt_positive` | string | No | "A person speaks naturally..." | Positive prompt |
| `quality_preset` | string | No | "high" | Quality: `fast`, `high`, `ultra` |
| `width` | int | No | 1280 | Output width |
| `height` | int | No | 736 | Output height |
| `seed` | int | No | random | Random seed for reproducibility |
| `lora_camera` | float | No | 0.3 | Camera LoRA (0 = disable dolly-in) |
| `lora_distilled` | float | No | 0.6 | Distilled LoRA strength |
| `lora_detailer` | float | No | 1.0 | Detailer LoRA strength |
| `img_compression` | int | No | 23 | Image compression (0-50, lower = better) |
| `img_strength` | float | No | 1.0 | First frame injection strength (0-1) |

---

## Mode 2: Audio Generation (Image + Duration)

Generate video AND audio from just an image and duration (no input audio required).

### Request Format

```json
{
  "input": {
    "image_url": "https://example.com/portrait.jpg",
    "duration": 5.0,
    "prompt_positive": "A person speaking about nature",
    "quality_preset": "high"
  }
}
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `image_url` | string | Yes | - | URL to portrait image (JPG/PNG) |
| `duration` | float | Yes | - | Video/audio duration in seconds (1-30) |
| `prompt_positive` | string | No | "A person speaking naturally..." | Positive prompt |
| `prompt_negative` | string | No | "blurry, low quality..." | Negative prompt |
| `quality_preset` | string | No | "high" | Quality: `fast`, `high`, `ultra` |
| `width` | int | No | 1280 | Output width |
| `height` | int | No | 736 | Output height |
| `seed` | int | No | random | Random seed for reproducibility |
| `lora_camera` | float | No | 0.3 | Camera LoRA (0 = disable dolly-in) |
| `lora_distilled` | float | No | 0.6 | Distilled LoRA strength |
| `lora_detailer` | float | No | 1.0 | Detailer LoRA strength |
| `img_compression` | int | No | 23 | Image compression (0-50, lower = better) |
| `img_strength` | float | No | 1.0 | First frame injection strength (0-1) |

### Audio Generation Notes

- Audio is generated at 25 Hz frame rate (LTX-2 native audio rate)
- Video is generated at 30 fps
- Both are combined into a single MP4 file
- Generated audio matches the visual content based on the prompt

---

## Common Parameters

### Quality Presets

| Preset | Steps | Distilled | Detailer | Camera | Use Case |
|--------|-------|-----------|----------|--------|----------|
| `fast` | 8 | 0.6 | 0.5 | 0.3 | Testing, iteration |
| `high` | 8 | 0.6 | 1.0 | 0.3 | Production (default) |
| `ultra` | 12 | 0.8 | 1.0 | 0.3 | Maximum quality |

### LoRA Parameters

| LoRA | Description | Range | Notes |
|------|-------------|-------|-------|
| `lora_camera` | Dolly-in camera effect | 0-1.0 | Set 0 to disable |
| `lora_distilled` | Inference acceleration | 0.4-0.8 | Lower = faster |
| `lora_detailer` | Detail enhancement | 0.5-1.0 | Higher = more detail |

### Image Parameters

| Parameter | Description | Range | Notes |
|-----------|-------------|-------|-------|
| `img_compression` | First frame compression | 0-50 | Lower = better quality, may cause initial freeze |
| `img_strength` | First frame injection | 0-1.0 | Lower = more animation freedom |

### Notes

- **Negative prompt**: Not effective at CFG=1.0 (current config uses distilled model)
- **Camera LoRA**: Creates a slow dolly-in (push) camera movement effect

---

## Response Format

### Mode 1 Success (Lip-sync)

```json
{
  "id": "job-id",
  "status": "COMPLETED",
  "output": {
    "status": "success",
    "output": {
      "video_url": "https://storage.googleapis.com/dramaland-public/ugc_media/{job_id}/ltx2_videos/{filename}.mp4",
      "gcs_url": "gs://dramaland-public/ugc_media/{job_id}/ltx2_videos/{filename}.mp4",
      "video_filename": "20260126_183520_ltx2_output_00001-audio.mp4",
      "video_size_bytes": 3167568,
      "resolution": "1280x736",
      "duration": "8.2s",
      "frames": 248,
      "fps": 30,
      "seed": 1769452070347,
      "quality_preset": "fast",
      "generation_time": 120.5
    }
  }
}
```

### Mode 2 Success (Audio Generation)

```json
{
  "id": "job-id",
  "status": "COMPLETED",
  "output": {
    "status": "success",
    "output": {
      "video_url": "https://storage.googleapis.com/dramaland-public/ugc_media/{job_id}/ltx2_videos/{filename}.mp4",
      "gcs_url": "gs://dramaland-public/ugc_media/{job_id}/ltx2_videos/{filename}.mp4",
      "video_filename": "20260127_120000_ltx2_output_00001-audio.mp4",
      "video_size_bytes": 2500000,
      "resolution": "1280x736",
      "duration": "5.0s",
      "frames": 151,
      "audio_frames": 125,
      "fps": 30,
      "seed": 1769452070347,
      "quality_preset": "high",
      "mode": "audio_gen",
      "generation_time": 90.5
    }
  }
}
```

### Error

```json
{
  "id": "job-id",
  "status": "FAILED",
  "error": "Failed to download image: 404 Not Found"
}
```

## Examples

### cURL - Mode 1: Lip-sync (Basic)

```bash
curl -X POST "https://api.runpod.ai/v2/42qdgmzjc9ldy5/run" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image_url": "https://example.com/portrait.jpg",
      "audio_url": "https://example.com/speech.mp3"
    }
  }'
```

### cURL - Mode 1: Disable Camera LoRA

```bash
curl -X POST "https://api.runpod.ai/v2/42qdgmzjc9ldy5/run" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image_url": "https://example.com/portrait.jpg",
      "audio_url": "https://example.com/speech.mp3",
      "lora_camera": 0
    }
  }'
```

### cURL - Mode 2: Audio Generation

```bash
curl -X POST "https://api.runpod.ai/v2/42qdgmzjc9ldy5/run" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image_url": "https://example.com/portrait.jpg",
      "duration": 5.0,
      "prompt_positive": "A person speaking about nature",
      "quality_preset": "high"
    }
  }'
```

### cURL - Mode 2: Fast Preview

```bash
curl -X POST "https://api.runpod.ai/v2/42qdgmzjc9ldy5/run" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image_url": "https://example.com/portrait.jpg",
      "duration": 3.0,
      "quality_preset": "fast"
    }
  }'
```

### Python - Mode 1 (Lip-sync)

```python
import requests
import time

API_KEY = "your_runpod_api_key"
ENDPOINT = "https://api.runpod.ai/v2/42qdgmzjc9ldy5"

def generate_lipsync_video(
    image_url: str,
    audio_url: str,
    quality: str = "high",
    lora_camera: float = 0.3
) -> dict:
    """Generate lip-synced video from image and audio."""

    response = requests.post(
        f"{ENDPOINT}/run",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "input": {
                "image_url": image_url,
                "audio_url": audio_url,
                "quality_preset": quality,
                "lora_camera": lora_camera
            }
        }
    )
    job_id = response.json()["id"]
    print(f"Job submitted: {job_id}")

    # Poll for completion
    while True:
        result = requests.get(
            f"{ENDPOINT}/status/{job_id}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        ).json()

        if result["status"] == "COMPLETED":
            return result["output"]["output"]
        if result["status"] == "FAILED":
            raise Exception(result.get("error", "Unknown error"))

        print(f"Status: {result['status']}")
        time.sleep(10)

# Usage
result = generate_lipsync_video(
    image_url="https://example.com/portrait.jpg",
    audio_url="https://example.com/speech.mp3",
    lora_camera=0  # Disable dolly-in effect
)
print(f"Video URL: {result['video_url']}")
```

### Python - Mode 2 (Audio Generation)

```python
def generate_video_with_audio(
    image_url: str,
    duration: float,
    prompt: str = "A person speaking naturally",
    quality: str = "high"
) -> dict:
    """Generate video AND audio from image and duration."""

    response = requests.post(
        f"{ENDPOINT}/run",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "input": {
                "image_url": image_url,
                "duration": duration,
                "prompt_positive": prompt,
                "quality_preset": quality
            }
        }
    )
    job_id = response.json()["id"]
    print(f"Job submitted: {job_id}")

    while True:
        result = requests.get(
            f"{ENDPOINT}/status/{job_id}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        ).json()

        if result["status"] == "COMPLETED":
            return result["output"]["output"]
        if result["status"] == "FAILED":
            raise Exception(result.get("error", "Unknown error"))

        print(f"Status: {result['status']}")
        time.sleep(10)

# Usage
result = generate_video_with_audio(
    image_url="https://example.com/portrait.jpg",
    duration=5.0,
    prompt="A person speaking about technology"
)
print(f"Video URL: {result['video_url']}")
print(f"Mode: {result['mode']}")  # "audio_gen"
```

### TypeScript

```typescript
interface VideoResult {
  video_url: string;
  gcs_url: string;
  video_filename: string;
  video_size_bytes: number;
  resolution: string;
  duration: string;
  frames: number;
  audio_frames?: number;  // Mode 2 only
  fps: number;
  seed: number;
  quality_preset: string;
  mode?: string;  // "audio_gen" for Mode 2
  generation_time: number;
}

const API_KEY = process.env.RUNPOD_API_KEY;
const ENDPOINT = 'https://api.runpod.ai/v2/42qdgmzjc9ldy5';

// Mode 1: Lip-sync
async function generateLipsyncVideo(
  imageUrl: string,
  audioUrl: string,
  options: { quality?: string; loraCamera?: number } = {}
): Promise<VideoResult> {
  const submitRes = await fetch(`${ENDPOINT}/run`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      input: {
        image_url: imageUrl,
        audio_url: audioUrl,
        quality_preset: options.quality || 'high',
        lora_camera: options.loraCamera ?? 0.3,
      },
    }),
  });
  const { id: jobId } = await submitRes.json();

  while (true) {
    const statusRes = await fetch(`${ENDPOINT}/status/${jobId}`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
    });
    const result = await statusRes.json();

    if (result.status === 'COMPLETED') return result.output.output;
    if (result.status === 'FAILED') throw new Error(result.error);

    await new Promise((r) => setTimeout(r, 10000));
  }
}

// Mode 2: Audio Generation
async function generateVideoWithAudio(
  imageUrl: string,
  duration: number,
  options: { prompt?: string; quality?: string } = {}
): Promise<VideoResult> {
  const submitRes = await fetch(`${ENDPOINT}/run`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      input: {
        image_url: imageUrl,
        duration: duration,
        prompt_positive: options.prompt || 'A person speaking naturally',
        quality_preset: options.quality || 'high',
      },
    }),
  });
  const { id: jobId } = await submitRes.json();

  while (true) {
    const statusRes = await fetch(`${ENDPOINT}/status/${jobId}`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
    });
    const result = await statusRes.json();

    if (result.status === 'COMPLETED') return result.output.output;
    if (result.status === 'FAILED') throw new Error(result.error);

    await new Promise((r) => setTimeout(r, 10000));
  }
}

// Usage - Mode 1
const lipsyncResult = await generateLipsyncVideo(
  'https://example.com/portrait.jpg',
  'https://example.com/speech.mp3',
  { loraCamera: 0 }
);

// Usage - Mode 2
const audioGenResult = await generateVideoWithAudio(
  'https://example.com/portrait.jpg',
  5.0,
  { prompt: 'A person speaking about technology' }
);
console.log(audioGenResult.mode);  // "audio_gen"
```

## Video Storage

Generated videos are stored in Google Cloud Storage:

```
https://storage.googleapis.com/dramaland-public/ugc_media/{job_id}/ltx2_videos/{filename}.mp4
```

## Performance

### Mode 1: Lip-sync

| Quality | Typical Time | Video Size |
|---------|-------------|------------|
| fast | 60-120s | ~3 MB |
| high | 120-180s | ~5 MB |
| ultra | 180-300s | ~8 MB |

*Times based on RTX 4090/5090, 10-second audio*

### Mode 2: Audio Generation

| Duration | Quality | Typical Time |
|----------|---------|-------------|
| 5s | fast | ~85s |
| 10s | fast | ~126s |
| 15s | fast | ~450s |

*Times based on RTX 4090/5090*

## Error Codes

| Error | Cause | Solution |
|-------|-------|----------|
| `Failed to download image` | Invalid image URL | Check URL accessibility |
| `Failed to download audio` | Invalid audio URL (Mode 1) | Check URL accessibility |
| `Duration must be at least 1 second` | duration < 1 (Mode 2) | Use duration >= 1.0 |
| `Duration cannot exceed 30 seconds` | duration > 30 (Mode 2) | Use duration <= 30.0 |
| `ComfyUI failed to start` | GPU initialization error | Retry request |
| `Generation timeout` | Processing exceeded 10 min | Use shorter duration or retry |
| `GCS upload failed` | Storage error | Video returned as base64 fallback |

## Limits

| Limit | Mode 1 (Lip-sync) | Mode 2 (Audio Gen) |
|-------|-------------------|-------------------|
| Max duration | ~30s (audio length) | 30s (duration param) |
| Min duration | 1s | 1s |
| Max file size | 50 MB per input | 50 MB (image only) |
| Concurrent jobs | Based on worker pool | Based on worker pool |
