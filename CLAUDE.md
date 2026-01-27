# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

LTX-2 Audio-to-Video RunPod Serverless API - generates lip-synced video from image + audio using the LTX-2 19B model.

## Architecture

```
User Request (image_url, audio_url, prompt)
    ↓
RunPod Serverless API (endpoint: 42qdgmzjc9ldy5)
    ↓
GPU Workers (RTX 4090/5090, 24GB+ VRAM)
    ├─ ComfyUI Framework
    ├─ LTX-2 19B Model (FP8)
    └─ LoRA Models (distilled, detailer, camera)
    ↓
GCS Upload (dramaland-public bucket)
    ↓
Return video_url
```

## File Structure

```
LTX/
├── CLAUDE.md
├── docker/
│   ├── Dockerfile                   # Worker container (v33)
│   ├── workflow_ltx2_enhanced.json  # ComfyUI workflow template
│   ├── API.md                       # API documentation
│   └── pod_files/
│       ├── rp_handler.py            # RunPod handler
│       ├── url_downloader.py        # URL downloader
│       ├── workflow_builder.py      # Workflow builder
│       ├── gcs_uploader.py          # GCS upload
│       ├── start_wrapper.sh         # Startup script
│       └── gcs-credentials.json     # GCS credentials
├── scripts/                         # Utility scripts
└── test/                            # Test files
```

## Key Commands

```bash
# Build & Push
cd docker
docker build --platform linux/amd64 -t nooka210/ltx2-comfyui-worker:v33 .
docker push nooka210/ltx2-comfyui-worker:v33

# Test API
curl -X POST "https://api.runpod.ai/v2/42qdgmzjc9ldy5/run" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input":{"image_url":"...","audio_url":"...","quality_preset":"fast"}}'
```

## API

**Endpoint**: `https://api.runpod.ai/v2/42qdgmzjc9ldy5`

| Method | Path | Description |
|--------|------|-------------|
| POST | /run | Async job submission |
| POST | /runsync | Sync job (wait for result) |
| GET | /status/{id} | Check job status |

See `docker/API.md` for full documentation.

## Models (Network Volume)

| Model | Size | File |
|-------|------|------|
| Checkpoint | ~26GB | `checkpoints/ltx-2-19b-dev-fp8.safetensors` |
| Text Encoder | ~12GB | `text_encoders/gemma_3_12B_it_fp8_scaled.safetensors` |
| LoRA Distilled | ~7.6GB | `loras/ltx-video-2b-v0.9.7-distilled-lora-384.safetensors` |
| LoRA Detailer | ~2.5GB | `loras/ltx-video-2b-v0.9.7-detailer-lora-768.safetensors` |
| LoRA Camera | ~313MB | `loras/ltx-video-2b-v0.9.5-camera-control-dolly-in-lora.safetensors` |

## LoRA 配置

| LoRA | 作用 | 默认强度 |
|------|------|---------|
| Distilled | 加速推理 | 0.6 |
| Detailer | 增强细节 | 1.0 |
| Camera (dolly-in) | 推镜头效果 | 0.3 |

## 图像参数

| 参数 | 作用 | 默认值 | 说明 |
|------|------|--------|------|
| img_compression | 首帧压缩 | 23 | 0-50，越低质量越好 |
| img_strength | 首帧注入 | 1.0 | 0-1，越低动画越自由 |

## Notes

- Video output: `gs://dramaland-public/ugc_media/{job_id}/ltx2_videos/`
- Network Volumes: `ltx2-models` (EU-RO-1), `ltx2-models-ustx3` (US-TX-3)
- Performance: ~60-120s for 10s video (quality: fast)
