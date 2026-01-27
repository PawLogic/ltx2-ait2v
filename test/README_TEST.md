# LTX-2 ComfyUI API 测试指南

## 方法 1: SSH Tunnel 测试（推荐）

### 步骤 1: 创建 SSH Tunnel
```bash
# 在新的终端窗口运行（保持运行）
ssh -L 8188:localhost:8188 root@82.221.170.234 -p 21286
```

### 步骤 2: 运行测试脚本
```bash
# 在另一个终端窗口运行
cd /Users/tangkaixin/Dev/LTX/test
python3 simple_test.py
```

### 步骤 3: 完整 API 测试
```bash
# 上传文件并生成视频
python3 test_api.py
```

---

## 方法 2: Jupyter Terminal 测试

### 访问 Jupyter
```
URL: https://kl34b69nag9f1b-8888.proxy.runpod.net
Token: igegckmc5ve9ezuodsib
```

### 在 Jupyter Terminal 中运行

#### 测试 1: 系统状态
```bash
curl localhost:8188/system_stats | python3 -m json.tool
```

#### 测试 2: LTX 节点列表
```bash
curl localhost:8188/object_info | python3 -c "import sys,json; data=json.load(sys.stdin); ltx=[k for k in data.keys() if 'LTX' in k.upper()]; print('LTX Nodes:', ltx)"
```

#### 测试 3: 检查模型
```bash
curl localhost:8188/object_info | python3 -c "import sys,json; data=json.load(sys.stdin); models=data.get('CheckpointLoaderSimple',{}).get('input',{}).get('required',{}).get('ckpt_name',[[]])[0]; print('Models:', [m for m in models if 'ltx' in m.lower()])"
```

#### 测试 4: 队列状态
```bash
curl localhost:8188/queue | python3 -m json.tool
```

---

## 方法 3: 直接在 Pod 上测试

### 上传测试脚本
```bash
scp -P 21286 simple_test.py root@82.221.170.234:/tmp/
```

### SSH 登录并运行
```bash
ssh root@82.221.170.234 -p 21286
cd /tmp
python3 simple_test.py
```

---

## API 端点说明

| 端点 | 方法 | 说明 |
|------|------|------|
| `/system_stats` | GET | 系统状态（VRAM, CPU, OS） |
| `/object_info` | GET | 所有可用节点和参数 |
| `/queue` | GET | 当前队列状态 |
| `/prompt` | POST | 提交工作流 |
| `/history/{prompt_id}` | GET | 查询执行历史 |
| `/upload/image` | POST | 上传图片/音频 |

---

## 预期输出

### System Stats
```json
{
  "system": {
    "os": "linux",
    "python_version": "3.12.3"
  },
  "devices": [{
    "name": "NVIDIA GeForce RTX 5090",
    "type": "cuda",
    "vram_total": 34464022528,
    "vram_free": 32000000000
  }]
}
```

### LTX Nodes (部分)
```
- LTXVAudioVAELoader
- LTXVAudioVAEEncode
- LTXVAudioVAEDecode
- LTXVEmptyLatentAudio
- LTXAVTextEncoderLoader
- LTXVImgToVideo
- LTXVLatentUpsampler
```

---

## 故障排除

### SSH Tunnel 无法连接
```bash
# 检查端口是否被占用
lsof -i :8188

# 杀死旧的 SSH tunnel
pkill -f "ssh.*8188:localhost:8188"

# 重新创建 tunnel
ssh -L 8188:localhost:8188 root@82.221.170.234 -p 21286
```

### ComfyUI 无响应
```bash
# SSH 登录 Pod
ssh root@82.221.170.234 -p 21286

# 检查 ComfyUI 进程
ps aux | grep "python main.py"

# 检查端口监听
ss -tlnp | grep 8188

# 重启 ComfyUI
pkill -f "python main.py"
cd /workspace/ComfyUI
python main.py --listen 0.0.0.0 --port 8188
```

### 模型未加载
```bash
# 检查模型文件
ls -lh /workspace/ComfyUI/models/diffusion_models/

# 应该看到
# ltx-2-19b-dev-fp8.safetensors  (~26GB)
```
