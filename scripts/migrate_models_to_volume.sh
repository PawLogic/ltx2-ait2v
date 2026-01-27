#!/bin/bash
# 将模型从测试 Pod 复制到 Network Volume

set -e

echo "========================================"
echo "LTX-2 模型迁移到 Network Volume"
echo "========================================"

# 源路径 (Pod workspace)
SRC_BASE="/workspace/ComfyUI/models"
# 目标路径 (Network Volume)
DEST_BASE="/runpod-volume/ComfyUI/models"

echo ""
echo "步骤 1: 创建目标目录结构"
echo "----------------------------------------"
mkdir -p "${DEST_BASE}/checkpoints"
mkdir -p "${DEST_BASE}/diffusion_models"
mkdir -p "${DEST_BASE}/loras"
echo "✅ 目录已创建"

echo ""
echo "步骤 2: 复制主模型 (~19GB)"
echo "----------------------------------------"
if [ -f "${SRC_BASE}/diffusion_models/ltx-2-19b-dev-fp8.safetensors" ]; then
    echo "从 diffusion_models 复制..."
    cp -v "${SRC_BASE}/diffusion_models/ltx-2-19b-dev-fp8.safetensors" \
       "${DEST_BASE}/checkpoints/"
elif [ -f "${SRC_BASE}/checkpoints/ltx-2-19b-dev-fp8.safetensors" ]; then
    echo "从 checkpoints 复制..."
    cp -v "${SRC_BASE}/checkpoints/ltx-2-19b-dev-fp8.safetensors" \
       "${DEST_BASE}/checkpoints/"
else
    echo "⚠️ 主模型不存在，尝试查找..."
    find ${SRC_BASE} -name "ltx-2-19b-dev-fp8.safetensors" -type f
fi

echo ""
echo "步骤 3: 复制音频处理模型"
echo "----------------------------------------"
# MelBandRoformer 可能在 checkpoints 或 diffusion_models
find ${SRC_BASE} -name "MelBandRoformer*" -type f -exec cp -v {} "${DEST_BASE}/diffusion_models/" \;

echo ""
echo "步骤 4: 复制 LoRA 文件"
echo "----------------------------------------"
if [ -d "${SRC_BASE}/loras" ]; then
    cp -v "${SRC_BASE}/loras"/ltx-2-19b-*.safetensors "${DEST_BASE}/loras/" 2>/dev/null || echo "⚠️ 部分 LoRA 文件未找到"
else
    echo "⚠️ loras 目录不存在"
fi

echo ""
echo "步骤 5: 验证文件完整性"
echo "========================================"
echo ""
echo "主模型 (checkpoints):"
ls -lh "${DEST_BASE}/checkpoints/" || echo "⚠️ 目录为空"

echo ""
echo "音频模型 (diffusion_models):"
ls -lh "${DEST_BASE}/diffusion_models/" || echo "⚠️ 目录为空"

echo ""
echo "LoRA 文件 (loras):"
ls -lh "${DEST_BASE}/loras/" || echo "⚠️ 目录为空"

echo ""
echo "========================================"
echo "✅ 模型迁移完成"
echo "========================================"
