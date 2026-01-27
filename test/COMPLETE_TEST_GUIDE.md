# LTX-2 视频生成完整测试指南

## 🚨 当前状态

- Pod ID: `kl34b69nag9f1b`
- ComfyUI: 运行中（端口 8188）
- LTX-2 模型: 已加载（26GB）
- 问题: SSH 连接不稳定

## 📋 方案 A: Jupyter Terminal 测试（推荐）

### 1. 访问 Jupyter

浏览器打开：
```
https://kl34b69nag9f1b-8888.proxy.runpod.net
Token: igegckmc5ve9ezuodsib
```

### 2. 打开 Terminal

点击 Jupyter 界面的 **Terminal** 图标

### 3. 上传测试文件

在 Terminal 中创建测试文件：

```bash
# 创建工作目录
mkdir -p /workspace/ltx_test
cd /workspace/ltx_test

# 下载测试图片（或通过 Jupyter 上传）
# 如果有外部链接可以用 wget，否则手动上传

# 确认ComfyUI运行
curl -s localhost:8188/system_stats | python3 -m json.tool | head -20
```

### 4. 创建测试脚本

在 Terminal 中复制粘贴以下内容：

```bash
cat > /workspace/ltx_test/test_generate.py << 'SCRIPT_END'
#!/usr/bin/env python3
import json
import time
import random
from urllib import request
import os

BASE_URL = "http://localhost:8188"

def upload_file(filepath):
    filename = os.path.basename(filepath)
    print(f"Uploading {filename}...")

    with open(filepath, 'rb') as f:
        data = f.read()

    boundary = 'Boundary' + ''.join(random.choices('0123456789', k=16))
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'
    ).encode() + data + f'\r\n--{boundary}--\r\n'.encode()

    req = request.Request(
        f"{BASE_URL}/upload/image",
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )

    with request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        print(f"✅ Uploaded: {result.get('name')}")
        return result.get('name')

# 上传文件
image_name = upload_file('/workspace/ltx_test/test_input.jpg')
audio_name = upload_file('/workspace/ltx_test/test_audio.mp3')

# 创建工作流
workflow = {
    "1": {"class_type": "LTXVAudioVAELoader", "inputs": {}},
    "2": {"class_type": "LTXVAudioVAEEncode", "inputs": {"audio": audio_name, "vae": ["1", 0]}},
    "3": {"class_type": "LoadImage", "inputs": {"image": image_name}},
    "4": {"class_type": "LTXAVTextEncoderLoader", "inputs": {}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": "A beautiful woman speaking naturally", "clip": ["4", 0]}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 0]}},
    "7": {"class_type": "UNETLoader", "inputs": {"unet_name": "ltx-2-19b-dev-fp8.safetensors"}},
    "8": {"class_type": "LTXVImgToVideo", "inputs": {"image": ["3", 0], "audio_latent": ["2", 0], "frame_rate": 24, "frames": 121}},
    "9": {"class_type": "KSampler", "inputs": {
        "seed": random.randint(0, 2**31),
        "steps": 20,
        "cfg": 3.0,
        "sampler_name": "euler",
        "scheduler": "simple",
        "denoise": 1.0,
        "model": ["7", 0],
        "positive": ["5", 0],
        "negative": ["6", 0],
        "latent_image": ["8", 0]
    }}
}

# 提交任务
print("\nSubmitting workflow...")
payload = {"prompt": workflow, "client_id": f"test_{int(time.time())}"}
req = request.Request(
    f"{BASE_URL}/prompt",
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'}
)

with request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    prompt_id = result.get('prompt_id')
    print(f"✅ Queued! Prompt ID: {prompt_id}")
    print(f"\nGeneration started!")
    print(f"Check output: /workspace/ComfyUI/output/")
    print(f"\nMonitor queue:")
    print(f"  curl localhost:8188/queue")
SCRIPT_END

chmod +x /workspace/ltx_test/test_generate.py
```

### 5. 运行测试

```bash
python3 /workspace/ltx_test/test_generate.py
```

### 6. 监控进度

```bash
# 查看队列状态
watch -n 2 'curl -s localhost:8188/queue | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Running: {len(d.get(\"queue_running\",[]))}, Pending: {len(d.get(\"queue_pending\",[]))}\")"'

# 或手动检查
curl localhost:8188/queue | python3 -m json.tool
```

### 7. 查看输出

```bash
# 等待几分钟后
ls -lht /workspace/ComfyUI/output/ | head -10

# 找到最新的 mp4 文件，在 Jupyter 文件浏览器中下载
```

---

## 📋 方案 B: 简化手动测试

如果 Python 脚本有问题，使用 curl 手动测试：

### 1. 准备文件

```bash
cd /workspace/ltx_test

# 确认文件存在
ls -lh test_input.jpg test_audio.mp3
```

### 2. 上传图片

```bash
curl -X POST http://localhost:8188/upload/image \
  -F "image=@test_input.jpg" \
  -F "overwrite=true"
```

### 3. 上传音频

```bash
curl -X POST http://localhost:8188/upload/image \
  -F "image=@test_audio.mp3" \
  -F "overwrite=true"
```

### 4. 提交最简工作流

```bash
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "1": {"class_type": "LTXVAudioVAELoader", "inputs": {}},
      "2": {"class_type": "LTXVAudioVAEEncode", "inputs": {"audio": "test_audio.mp3", "vae": ["1", 0]}},
      "3": {"class_type": "LoadImage", "inputs": {"image": "test_input.jpg"}},
      "4": {"class_type": "LTXAVTextEncoderLoader", "inputs": {}},
      "5": {"class_type": "CLIPTextEncode", "inputs": {"text": "woman speaking", "clip": ["4", 0]}},
      "6": {"class_type": "UNETLoader", "inputs": {"unet_name": "ltx-2-19b-dev-fp8.safetensors"}},
      "7": {"class_type": "LTXVImgToVideo", "inputs": {"image": ["3", 0], "audio_latent": ["2", 0], "frame_rate": 24, "frames": 121}}
    },
    "client_id": "manual_test"
  }'
```

---

## 🔍 故障排除

### ComfyUI 没有响应

```bash
# 检查进程
ps aux | grep "python main.py" | grep -v grep

# 重启 ComfyUI
pkill -f "python main.py"
cd /workspace/ComfyUI
nohup python main.py --listen 0.0.0.0 --port 8188 > /tmp/comfyui.log 2>&1 &

# 等待10秒
sleep 10
curl localhost:8188/system_stats | python3 -m json.tool
```

### 模型文件检查

```bash
# 检查主模型
ls -lh /workspace/ComfyUI/models/diffusion_models/ltx-2-19b-dev-fp8.safetensors

# 检查 VAE（可能需要）
ls -lh /workspace/ComfyUI/models/vae/

# 检查音频模型
ls -lh /workspace/ComfyUI/models/checkpoints/
```

### 查看日志

```bash
# ComfyUI 日志
tail -f /tmp/comfyui.log

# 或查看用户日志
tail -f /workspace/ComfyUI/user/comfyui.log
```

---

## 📊 预期结果

- **队列提交**: ✅ 应该返回 prompt_id
- **生成时间**: 约 2-5 分钟（取决于 GPU 和参数）
- **输出文件**: `/workspace/ComfyUI/output/ltx2_test_XXXXX.mp4`
- **视频长度**: ~5 秒（121 帧）
- **分辨率**: 与输入图片匹配

---

## 📞 需要帮助？

如果遇到问题：
1. 截图错误信息
2. 复制相关日志
3. 记录步骤编号

当前 Pod 信息：
- Pod ID: kl34b69nag9f1b
- Jupyter: https://kl34b69nag9f1b-8888.proxy.runpod.net
- Token: igegckmc5ve9ezuodsib
