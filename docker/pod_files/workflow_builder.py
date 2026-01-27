#!/usr/bin/env python3
"""
Workflow template loader with placeholder injection.
Uses workflow_ltx2_enhanced.json as base template.

Based on test_720p.py production configuration:
- Resolution: 1280x736
- img_compression: 23
- fps: 30
- steps: 8
- cfg: 1.0
"""
import json
import math
import copy
from typing import Dict, Any


class WorkflowBuilder:
    """Build workflow from enhanced template with parameter injection."""

    def __init__(self, template_path: str = "/comfyui/workflows/ltx2_enhanced.json"):
        """Load enhanced workflow template."""
        with open(template_path, 'r') as f:
            self.template = json.load(f)

    def build_workflow(
        self,
        image_name: str,
        audio_name: str,
        audio_duration: float,
        prompt_positive: str,
        prompt_negative: str,
        seed: int,
        width: int = 1280,
        height: int = 736,
        fps: int = 30,
        steps: int = 8,
        cfg_scale: float = 1.0,
        lora_distilled: float = 0.6,
        lora_detailer: float = 1.0,
        lora_camera: float = 0.3,
        img_compression: int = 23,
        img_strength: float = 1.0,
    ) -> dict:
        """
        Inject parameters into workflow template.

        Args:
            image_name: Uploaded image filename in ComfyUI
            audio_name: Uploaded audio filename in ComfyUI
            audio_duration: Audio duration in seconds
            prompt_positive: Positive prompt text
            prompt_negative: Negative prompt text
            seed: Random seed for generation
            width: Video width (must be divisible by 32)
            height: Video height (must be divisible by 32)
            fps: Frames per second (default 30)
            steps: Sampling steps (default 8)
            cfg_scale: CFG scale (default 1.0)
            lora_distilled: Distilled LoRA strength (default 0.6)
            lora_detailer: Detailer LoRA strength (default 1.0)
            lora_camera: Camera LoRA strength (default 0.3)
            img_compression: Image compression level (default 23, lower = better quality)
            img_strength: First frame injection strength (default 0.9)

        Returns:
            Complete workflow ready for ComfyUI execution
        """
        # Calculate frame count to ensure video duration >= audio duration
        # Formula: num_frames = ceil(audio_duration * fps) + buffer
        # Buffer ensures video is never shorter than audio
        # If audio is 10.0s at 30fps = 300 frames, we use 300 frames = 10.0s video
        num_frames = math.ceil(audio_duration * fps)

        # Add 1 frame buffer to ensure video covers full audio
        num_frames += 1

        # Ensure minimum frames (at least 1 second of video)
        if num_frames < 30:
            num_frames = 30

        # Create parameter mapping for placeholder replacement
        params = {
            "INPUT_IMAGE": image_name,
            "INPUT_AUDIO": audio_name,
            "WIDTH": width,
            "HEIGHT": height,
            "NUM_FRAMES": num_frames,
            "AUDIO_DURATION": audio_duration,
            "FPS": fps,
            "PROMPT_POSITIVE": prompt_positive,
            "PROMPT_NEGATIVE": prompt_negative,
            "SEED": seed,
            "STEPS": steps,
            "CFG_SCALE": cfg_scale,
            "LORA_DISTILLED_STRENGTH": lora_distilled,
            "LORA_DETAILER_STRENGTH": lora_detailer,
            "LORA_CAMERA_STRENGTH": lora_camera,
            "IMG_COMPRESSION": img_compression,
            "IMG_STRENGTH": img_strength,
        }

        # Deep copy template and inject parameters
        workflow = self._inject_parameters(self.template, params)

        return workflow

    def _inject_parameters(self, workflow: dict, params: Dict[str, Any]) -> dict:
        """Recursively replace placeholders with actual values."""
        workflow = copy.deepcopy(workflow)

        def replace_value(obj):
            if isinstance(obj, str):
                # Check if this string is a placeholder key
                if obj in params:
                    return params[obj]
                return obj
            elif isinstance(obj, dict):
                return {k: replace_value(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_value(item) for item in obj]
            else:
                return obj

        return replace_value(workflow)

    def get_video_params(self, audio_duration: float, fps: int = 30) -> dict:
        """
        Calculate video parameters from audio duration.
        Ensures video duration >= audio duration.

        Args:
            audio_duration: Audio duration in seconds
            fps: Frames per second

        Returns:
            dict with num_frames, actual_duration, fps, audio_duration
        """
        # Ensure video is at least as long as audio (with 1 frame buffer)
        num_frames = math.ceil(audio_duration * fps) + 1
        if num_frames < 30:
            num_frames = 30

        return {
            "num_frames": num_frames,
            "actual_duration": num_frames / fps,
            "audio_duration": audio_duration,
            "fps": fps,
        }
