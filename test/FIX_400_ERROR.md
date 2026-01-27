# 修复 HTTP 400 错误指南

## 🔴 问题分析

你遇到的 400 错误是因为远程服务器上的 `test_generate.py` 脚本在创建时被截断了：

```python
# 错误的脚本内容（被截断）
audio_name = e('/workspace/ltx_test/test_audio.mp3')  # ❌ 应该是 upload_file
```

## ✅ 解决方案：通过 Jupyter 上传正确的脚本

### 方法 1: 直接上传（推荐）

1. **访问 Jupyter**
   ```
   https://kl34b69nag9f1b-8888.proxy.runpod.net
   Token: igegckmc5ve9ezuodsib
   ```

2. **上传脚本文件**
   - 点击右上角 "Upload" 按钮
   - 选择本地的 `test/test_simple.py` 文件（这个文件在你的电脑上）
   - 上传完成后，将文件移动到 `/workspace/ltx_test/` 目录

3. **设置权限**
   在 Jupyter Terminal 中运行：
   ```bash
   chmod +x /workspace/ltx_test/test_simple.py
   ```

4. **运行测试**
   ```bash
   cd /workspace/ltx_test
   python3 test_simple.py
   ```

### 方法 2: 使用 curl 直接测试（最简单）

如果上传脚本有问题，直接用 curl 测试：

```bash
cd /workspace/ltx_test

# 1. 检查 ComfyUI 状态
curl -s localhost:8188/system_stats | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"ComfyUI {d['system']['comfyui_version']} - OK\")"

# 2. 上传文件（已完成，跳过）
# 文件已在: test_input.jpg, test_audio.mp3

# 3. 提交最简工作流
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "1": {"class_type": "LTXVAudioVAELoader", "inputs": {}},
      "2": {"class_type": "LTXVAudioVAEEncode", "inputs": {"audio": "test_audio.mp3", "vae": ["1", 0]}},
      "3": {"class_type": "LoadImage", "inputs": {"image": "test_input.jpg"}},
      "4": {"class_type": "LTXAVTextEncoderLoader", "inputs": {}},
      "5": {"class_type": "CLIPTextEncode", "inputs": {"text": "woman speaking", "clip": ["4", 0]}},
      "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 0]}},
      "7": {"class_type": "UNETLoader", "inputs": {"unet_name": "ltx-2-19b-dev-fp8.safetensors"}},
      "8": {"class_type": "LTXVImgToVideo", "inputs": {"image": ["3", 0], "audio_latent": ["2", 0], "frame_rate": 24, "frames": 121}}
    },
    "client_id": "curl_test"
  }'
```

**预期输出**：
```json
{
  "prompt_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "number": 1,
  "node_errors": {}
}
```

如果还是 400 错误，检查响应：
```bash
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '...' 2>&1 | python3 -m json.tool
```

### 方法 3: 检查节点可用性

如果 curl 也失败，可能是节点类型不对：

```bash
# 检查可用的节点类型
curl -s localhost:8188/object_info | python3 -m json.tool | grep -A 5 "LTXVAudioVAELoader"

# 列出所有 LTX 相关节点
curl -s localhost:8188/object_info | python3 -c "import sys,json; nodes=json.load(sys.stdin); [print(k) for k in nodes.keys() if 'LTX' in k or 'ltx' in k.lower()]"
```

## 🔍 调试步骤

### 1. 验证文件存在
```bash
ls -lh /workspace/ltx_test/test_input.jpg
ls -lh /workspace/ltx_test/test_audio.mp3
```

### 2. 验证模型文件
```bash
ls -lh /workspace/ComfyUI/models/diffusion_models/ltx-2-19b-dev-fp8.safetensors
```

### 3. 检查 ComfyUI 日志
```bash
# 查看最近的错误
tail -50 /tmp/comfyui.log | grep -i error

# 实时监控
tail -f /tmp/comfyui.log
```

### 4. 测试基础功能
```bash
# 测试文件上传
curl -X POST http://localhost:8188/upload/image \
  -F "image=@test_input.jpg" \
  -F "overwrite=true"

# 应该返回：{"name": "test_input.jpg", ...}
```

## 📊 常见错误和解决方案

### 错误 1: "Node not found"
```json
{
  "error": "Node LTXVAudioVAELoader not found",
  "node_errors": {"1": {...}}
}
```

**解决**：检查自定义节点是否已安装
```bash
ls -la /workspace/ComfyUI/custom_nodes/ | grep -i ltx
```

### 错误 2: "Invalid input"
```json
{
  "error": "Invalid input for node 2",
  "node_errors": {"2": {...}}
}
```

**解决**：检查输入参数类型和格式

### 错误 3: "File not found"
```json
{
  "error": "File test_audio.mp3 not found"
}
```

**解决**：确认文件已上传到 `/workspace/ComfyUI/input/`
```bash
cp /workspace/ltx_test/test_audio.mp3 /workspace/ComfyUI/input/
cp /workspace/ltx_test/test_input.jpg /workspace/ComfyUI/input/
```

## 🎯 快速验证脚本

创建一个最小测试脚本：

```bash
cat > /workspace/ltx_test/quick_test.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Quick LTX-2 Test ==="

# 1. 检查 ComfyUI
echo "1. Checking ComfyUI..."
curl -s localhost:8188/system_stats > /dev/null && echo "   ✅ ComfyUI OK" || exit 1

# 2. 检查模型
echo "2. Checking model..."
test -f /workspace/ComfyUI/models/diffusion_models/ltx-2-19b-dev-fp8.safetensors && \
  echo "   ✅ Model OK" || exit 1

# 3. 检查测试文件
echo "3. Checking test files..."
test -f /workspace/ltx_test/test_input.jpg && echo "   ✅ Image OK" || exit 1
test -f /workspace/ltx_test/test_audio.mp3 && echo "   ✅ Audio OK" || exit 1

# 4. 提交测试
echo "4. Submitting test workflow..."
RESPONSE=$(curl -s -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "1": {"class_type": "LTXVAudioVAELoader", "inputs": {}},
      "2": {"class_type": "LoadImage", "inputs": {"image": "test_input.jpg"}}
    },
    "client_id": "quick_test"
  }')

echo "$RESPONSE" | python3 -m json.tool

if echo "$RESPONSE" | grep -q "prompt_id"; then
  echo "   ✅ Workflow accepted!"
else
  echo "   ❌ Workflow rejected!"
  exit 1
fi

echo "=== Test Complete ==="
EOF

chmod +x /workspace/ltx_test/quick_test.sh
bash /workspace/ltx_test/quick_test.sh
```

## 📞 下一步

1. **立即尝试**: 使用方法 2 的 curl 命令测试
2. **如果成功**: 上传完整的 `test_simple.py` 脚本
3. **如果失败**: 运行调试步骤，提供错误输出

需要我帮你分析具体的错误输出吗？
