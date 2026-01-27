#!/bin/bash
# 下载缺失的 LoRA 和音频模型到测试 Pod

set -e

echo "========================================"
echo "下载缺失的 LTX-2 模型"
echo "========================================"

BASE="/workspace/ComfyUI/models"

echo ""
echo "步骤 1: 下载音频处理模型 (MelBandRoformer)"
echo "----------------------------------------"
cd "${BASE}/diffusion_models"
wget -c https://huggingface.co/Kijai/MelBandRoFormer_comfy/resolve/main/MelBandRoformer_fp16.safetensors
ls -lh MelBandRoformer_fp16.safetensors

echo ""
echo "步骤 2: 下载 LoRA 文件 (3个)"
echo "----------------------------------------"
cd "${BASE}/loras"

echo "下载 distilled-lora-384..."
wget -c https://huggingface.co/Lightricks/LTX-2/resolve/main/ltx-2-19b-distilled-lora-384.safetensors

echo "下载 ic-lora-detailer..."
wget -c https://huggingface.co/Lightricks/LTX-2-19b-IC-LoRA-Detailer/resolve/main/ltx-2-19b-ic-lora-detailer.safetensors

echo "下载 camera-control-dolly-in..."
wget -c https://huggingface.co/Lightricks/LTX-2-19b-LoRA-Camera-Control-Dolly-In/resolve/main/ltx-2-19b-lora-camera-control-dolly-in.safetensors

echo ""
echo "步骤 3: 验证文件"
echo "========================================"
ls -lh

echo ""
echo "✅ 模型下载完成"
