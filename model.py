"""
model.py — IntelliEye
Gemma 4 E4B / E2B model wrapper
Made by Hyunho Cho
"""

import json
import os
import re
import subprocess
import sys

import torch
from PIL import Image

# Check torchvision import — auto-install if missing
try:
    import torchvision  # noqa: F401
except ImportError:
    print("[IntelliEye] torchvision is not installed. Attempting automatic installation...", flush=True)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "torchvision", "-q"]
        )
        import torchvision  # noqa: F401
        print("[IntelliEye] torchvision installed successfully!")
    except Exception as e:
        print(
            f"[IntelliEye] torchvision auto-install failed: {e}\n"
            "Please install it manually:\n"
            "  pip install torchvision\n"
            "Or:\n"
            "  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
        )
        sys.exit(1)

from transformers import AutoModelForCausalLM, AutoProcessor

MODEL_IDS = {
    "E4B": "google/gemma-4-E4B-it",
    "E2B": "google/gemma-4-E2B-it",
}

SYSTEM_PROMPT = """You are an AI agent that watches the laptop screen in real time and accomplishes the user's goal.
Analyze the screen image and return exactly one next action in one of the JSON formats below.
Do not include any other text. Return JSON only.

Available actions:
{"action":"click","x":int,"y":int,"description":"description"}
{"action":"type","text":"text to type","description":"description"}
{"action":"hotkey","keys":["ctrl","c"],"description":"description"}
{"action":"scroll","direction":"up or down","amount":int,"description":"description"}
{"action":"screenshot","description":"use when only screen analysis is needed"}
{"action":"done","description":"use when the goal has been achieved"}

x, y coordinates are in screen pixels."""


def _detect_device() -> str:
    """Return the best available device (cuda > mps > cpu).

    Can be overridden with the INTELLIEYE_DEVICE environment variable.
    """
    env_device = os.environ.get("INTELLIEYE_DEVICE", "").strip().lower()
    if env_device in ("cuda", "mps", "cpu"):
        return env_device

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _has_meta_params(model) -> bool:
    """Return True if any model parameter is on the meta device."""
    for param in model.parameters():
        if param.device.type == "meta":
            return True
    return False


def _load_model(model_id: str, device: str, safe_load: bool):
    """Load the model according to device and safe-load options.

    Args:
        model_id: HuggingFace model ID
        device: "cuda", "mps", or "cpu"
        safe_load: When True, load with options that prevent meta tensors

    Returns:
        Loaded model
    """
    if device == "cuda" and not safe_load:
        return AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )

    # CPU / MPS or safe_load mode: avoid meta tensors by using
    # device_map=None, low_cpu_mem_usage=False, float32
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map=None,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=False,
    )
    model = model.to(device)
    return model


class GemmaAgent:
    """Load a Gemma 4 E4B or E2B model and decide screen-based actions."""

    def __init__(self, model_name: str):
        """
        Args:
            model_name: "E4B" or "E2B"
        """
        model_id = MODEL_IDS.get(model_name.upper(), MODEL_IDS["E4B"])
        print(f"  Loading model: {model_id}", flush=True)
        print("  (First run: downloading model weights — this may take several minutes...)", flush=True)

        device = _detect_device()
        safe_load = os.environ.get("INTELLIEYE_SAFE_LOAD", "").strip() == "1"
        print(f"  Device: {device}" + (" (safe-load mode)" if safe_load or device != "cuda" else ""), flush=True)

        print("  Loading processor...", flush=True)
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

        # Set pad token to EOS if missing
        if self.processor.tokenizer.pad_token_id is None:
            self.processor.tokenizer.pad_token_id = self.processor.tokenizer.eos_token_id

        print("  Loading model weights (this may take a while)...", flush=True)
        self.model = _load_model(model_id, device, safe_load)

        # If meta tensors are detected, retry with safe-load mode
        if _has_meta_params(self.model):
            print(
                "  ⚠️  Meta tensors detected. Retrying with safe-load mode...", flush=True
            )
            device = "cpu"
            self.model = _load_model(model_id, device, safe_load=True)

        # Set pad/EOS token IDs in generation_config
        eos_id = self.processor.tokenizer.eos_token_id
        if hasattr(self.model, "generation_config"):
            if self.model.generation_config.pad_token_id is None:
                self.model.generation_config.pad_token_id = eos_id
            if self.model.generation_config.eos_token_id is None:
                self.model.generation_config.eos_token_id = eos_id

        self.device = device
        self.model_name = model_name
        print("  ✅ Model loaded successfully!", flush=True)

    def decide_action(
        self,
        screen_image: Image.Image,
        goal: str,
        history: list,
    ) -> dict:
        """
        Decide the next action based on the current screen and goal.

        Args:
            screen_image: PIL Image of the current screen
            goal: Goal string requested by the user
            history: List of previous action strings

        Returns:
            Action dictionary
        """
        history_text = ""
        if history:
            history_text = "\nPrevious actions:\n" + "\n".join(
                f"  - {h}" for h in history[-5:]
            )

        user_text = (
            f"Goal: {goal}{history_text}\n\n"
            "Analyze the current screen and return the next action as JSON."
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": screen_image},
                    {"type": "text", "text": SYSTEM_PROMPT + "\n\n" + user_text},
                ],
            }
        ]

        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_tensors="pt",
            return_dict=True,
        )
        inputs = inputs.to(next(self.model.parameters()).device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,
        )

        # Decode only the generated tokens (after input)
        input_ids = inputs["input_ids"] if isinstance(inputs, dict) else inputs
        input_len = input_ids.shape[1]
        generated_ids = outputs[0][input_len:]
        response_text = self.processor.decode(generated_ids, skip_special_tokens=True).strip()

        return self._parse_json(response_text)

    def _parse_json(self, text: str) -> dict:
        """Extract a JSON dictionary from the response text."""
        # Remove code block markers
        text = re.sub(r"```(?:json)?", "", text).strip()

        # Find JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Fall back to screenshot action on parse failure
        return {"action": "screenshot", "description": f"Parse failed (raw: {text[:100]})"}
