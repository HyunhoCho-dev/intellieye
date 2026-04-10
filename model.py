"""
model.py — IntelliEye
Gemma 3n E4B / E2B model wrapper
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

from transformers import AutoModelForImageTextToText, AutoProcessor

# Import GatedRepoError for graceful auth error handling.
# huggingface_hub >= 0.21 exposes it in huggingface_hub.errors;
# older versions may not have it, so we fall back to a plain Exception alias.
try:
    from huggingface_hub.errors import GatedRepoError
except ImportError:
    try:
        from huggingface_hub.utils import GatedRepoError  # type: ignore[no-redef]
    except ImportError:
        GatedRepoError = None  # type: ignore[assignment,misc]

MODEL_IDS = {
    "E4B": "google/gemma-3n-E4B-it",
    "E2B": "google/gemma-3n-E2B-it",
}


def _gated_access_message(model_id: str) -> str:
    """Return a user-friendly message explaining how to unlock a gated HF model."""
    hf_url = f"https://huggingface.co/{model_id}"
    return (
        f"\n❌ Access Denied: '{model_id}' is a gated model on Hugging Face.\n\n"
        "  To use this model you need to:\n"
        f"    1. Visit {hf_url}\n"
        "       and click 'Agree and access repository' to accept the license.\n"
        "    2. Create a Hugging Face account if you don't have one (free):\n"
        "       https://huggingface.co/join\n"
        "    3. Generate a read token at:\n"
        "       https://huggingface.co/settings/tokens\n"
        "    4. Log in from your terminal:\n"
        "         huggingface-cli login\n"
        "       (paste your token when prompted)\n"
        "    5. Restart IntelliEye and try again.\n\n"
        "  Alternatively, set the HUGGING_FACE_HUB_TOKEN environment variable:\n"
        "    Windows PowerShell:\n"
        "      $env:HUGGING_FACE_HUB_TOKEN = 'hf_your_token_here'\n"
        "      intellieye\n"
    )

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
        return AutoModelForImageTextToText.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )

    # CPU / MPS or safe_load mode: avoid meta tensors by using
    # device_map=None, low_cpu_mem_usage=False, float32
    model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        device_map=None,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=False,
    )
    model = model.to(device)
    return model


def _is_gated_error(exc: BaseException) -> bool:
    """Return True if the exception indicates a gated/unauthorized HF model access."""
    # Direct GatedRepoError from huggingface_hub (if available)
    if GatedRepoError is not None and isinstance(exc, GatedRepoError):
        return True
    # Fallback: inspect the exception message for telltale strings
    msg = str(exc).lower()
    return (
        "gated" in msg
        or ("401" in msg and "huggingface" in msg)
        or "access to model" in msg
        or ("restricted" in msg and "authenticate" in msg)
    )


class GemmaAgent:
    """Load a Gemma 3n E4B or E2B model and decide screen-based actions."""

    def __init__(self, model_name: str):
        """
        Args:
            model_name: "E4B" or "E2B"

        Raises:
            SystemExit: if the model is gated and the user is not authenticated.
            RuntimeError: if meta tensors are detected and safe-load also fails.
        """
        model_id = MODEL_IDS.get(model_name.upper(), MODEL_IDS["E4B"])
        print(f"  Loading model: {model_id}", flush=True)
        print("  (First run: downloading model weights — this may take several minutes...)", flush=True)

        device = _detect_device()
        safe_load = os.environ.get("INTELLIEYE_SAFE_LOAD", "").strip() == "1"
        print(f"  Device: {device}" + (" (safe-load mode)" if safe_load or device != "cuda" else ""), flush=True)

        print("  Loading processor...", flush=True)
        try:
            self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        except Exception as exc:
            if _is_gated_error(exc):
                print(_gated_access_message(model_id), flush=True)
                sys.exit(1)
            raise

        # Set pad token to EOS if missing (access tokenizer safely)
        tok = getattr(self.processor, "tokenizer", None)
        if tok is not None and tok.pad_token_id is None:
            tok.pad_token_id = tok.eos_token_id

        print("  Loading model weights (this may take a while)...", flush=True)
        try:
            self.model = _load_model(model_id, device, safe_load)
        except Exception as exc:
            if _is_gated_error(exc):
                print(_gated_access_message(model_id), flush=True)
                sys.exit(1)
            raise

        # If meta tensors are detected, retry with safe-load mode
        if _has_meta_params(self.model):
            print(
                "  ⚠️  Meta tensors detected. Retrying with safe-load mode...", flush=True
            )
            device = "cpu"
            self.model = _load_model(model_id, device, safe_load=True)

        # Set pad/EOS token IDs in generation_config
        tok = getattr(self.processor, "tokenizer", None)
        eos_id = tok.eos_token_id if tok is not None else None
        if eos_id is not None and hasattr(self.model, "generation_config"):
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
                    {"type": "image"},
                    {"type": "text", "text": SYSTEM_PROMPT + "\n\n" + user_text},
                ],
            }
        ]

        # Apply chat template to get the formatted text prompt
        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        # Process text and image together (Gemma 3n multimodal API)
        inputs = self.processor(
            text=text,
            images=[screen_image],
            return_tensors="pt",
        )
        inputs = inputs.to(next(self.model.parameters()).device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,
        )

        # Decode only the generated tokens (after input)
        input_len = inputs["input_ids"].shape[1]
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
