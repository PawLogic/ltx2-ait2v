# 在 Jupyter 上运行 LTX-2 视频生成测试

## 步骤 1: 访问 Jupyter

打开浏览器访问：
```
URL: https://kl34b69nag9f1b-8888.proxy.runpod.net
Token: igegckmc5ve9ezuodsib
```

## 步骤 2: 上传测试文件

在 Jupyter 中：
1. 点击 Upload 按钮
2. 上传以下文件：
   - `test_input.jpg` (5.8 MB)
   - `test_audio.mp3` (373 KB)
   - `generate_on_pod.py`

或者在 Terminal 中运行：
```bash
cd /workspace
# 文件会通过其他方式传输到这里
```

## 步骤 3: 在 Terminal 中运行

打开 Jupyter Terminal，运行：

```bash
# 检查 ComfyUI 状态
curl localhost:8188/system_stats | python3 -m json.tool

# 运行生成脚本
cd /workspace
python3 generate_on_pod.py
```

## 步骤 4: 手动 API 测试（备选）

如果脚本有问题，手动测试：

```bash
# 1. 上传图片
curl -X POST http://localhost:8188/upload/image \
  -F "image=@test_input.jpg" \
  -F "overwrite=true"

# 2. 上传音频
curl -X POST http://localhost:8188/upload/image \
  -F "image=@test_audio.mp3" \
  -F "overwrite=true"

# 3. 提交工作流
cat > workflow.json << 'EOF'
{
  "prompt": {
    "1": {"class_type": "LTXVAudioVAELoader", "inputs": {}},
    "2": {"class_type": "LTXVAudioVAEEncode", "inputs": {"audio": "test_audio.mp3", "vae": ["1", 0]}},
    "3": {"class_type": "LoadImage", "inputs": {"image": "test_input.jpg"}},
    "4": {"class_type": "LTXAVTextEncoderLoader", "inputs": {}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": "woman speaking", "clip": ["4", 0]}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 0]}},
    "7": {"class_type": "UNETLoader", "inputs": {"unet_name": "ltx-2-19b-dev-fp8.safetensors"}},
    "8": {"class_type": "LTXVImgToVideo", "inputs": {"image": ["3", 0], "audio_latent": ["2", 0], "frame_rate": 24, "frames": 121}},
    "9": {"class_type": "KSampler", "inputs": {"seed": 42, "steps": 20, "cfg": 3.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0, "model": ["7", 0], "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["8", 0]}}
  },
  "client_id": "test_manual"
}
EOF

curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d @workflow.json

# 4. 检查队列
curl http://localhost:8188/queue | python3 -m json.tool
```

## 步骤 5: 查看输出

```bash
# 查看输出目录
ls -lh /workspace/ComfyUI/output/

# 查看最新生成的文件
ls -lt /workspace/ComfyUI/output/ | head -10

# 下载视频（在 Jupyter 文件浏览器中）
# 找到 output 文件夹，右键点击视频文件 -> Download
```

## 预期输出

- 视频文件名：`ltx2_test_XXXXX.mp4`
- 位置：`/workspace/ComfyUI/output/`
- 时长：~5 秒（121 帧 @ 24fps）
- 分辨率：与输入图片相同

## 故障排除

### ComfyUI 未运行
```bash
ps aux | grep "python main.py"
# 如果没有运行：
cd /workspace/ComfyUI
python main.py --listen 0.0.0.0 --port 8188 &
```

### 模型未找到
```bash
ls -lh /workspace/ComfyUI/models/diffusion_models/
# 应该看到：ltx-2-19b-dev-fp8.safetensors (~26GB)
```

### VAE 错误
```bash
# 检查 VAE 文件
ls -lh /workspace/ComfyUI/models/vae/
# 如果缺少，需要下载 ltx-2-vae.safetensors
```
