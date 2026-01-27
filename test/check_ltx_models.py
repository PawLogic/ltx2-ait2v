#!/usr/bin/env python3
"""Check LTX-2 model loading in ComfyUI"""
import json
from urllib import request

BASE_URL = "http://localhost:8188"

try:
    print("Checking LTX-specific loaders...")
    req = request.Request(f"{BASE_URL}/object_info")
    with request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    # Check LTXVAudioVAELoader
    if 'LTXVAudioVAELoader' in data:
        loader_info = data['LTXVAudioVAELoader']
        if 'input' in loader_info and 'required' in loader_info['input']:
            model_name_field = loader_info['input']['required'].get('model_name', [])
            if model_name_field:
                available_models = model_name_field[0] if isinstance(model_name_field, list) else []
                print(f"✅ LTXVAudioVAELoader models:")
                for model in available_models:
                    print(f"   - {model}")

    # Check if there's a specific LTX model loader
    ltx_loaders = [k for k in data.keys() if 'load' in k.lower() and 'ltx' in k.lower()]
    print(f"\n✅ Found {len(ltx_loaders)} LTX loader nodes:")
    for loader in ltx_loaders:
        print(f"   - {loader}")
        if 'input' in data[loader] and 'required' in data[loader]['input']:
            for param, value in data[loader]['input']['required'].items():
                if 'model' in param.lower() or 'name' in param.lower():
                    if isinstance(value, list) and len(value) > 0:
                        print(f"     {param}: {value[0][:3] if isinstance(value[0], list) else value[0]}")

    # Check UNETLoader (ComfyUI's diffusion model loader)
    if 'UNETLoader' in data:
        loader_info = data['UNETLoader']
        if 'input' in loader_info and 'required' in loader_info['input']:
            unet_models = loader_info['input']['required'].get('unet_name', [[]])[0]
            print(f"\n✅ UNETLoader models ({len(unet_models)}):")
            for model in unet_models:
                print(f"   - {model}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
