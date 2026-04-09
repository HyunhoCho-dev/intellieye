"""
model.py — IntelliEye
Gemma 4 E4B / E2B 모델 래퍼
Made by Hyunho Cho
"""

import json
import os
import re
import subprocess
import sys

import torch
from PIL import Image

# torchvision 임포트 확인 — 없으면 자동 설치 시도
try:
    import torchvision  # noqa: F401
except ImportError:
    print("[IntelliEye] torchvision이 설치되어 있지 않습니다. 자동으로 설치를 시도합니다...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "torchvision", "-q"]
        )
        import torchvision  # noqa: F401
        print("[IntelliEye] torchvision 설치 완료!")
    except Exception as e:
        print(
            f"[IntelliEye] torchvision 자동 설치 실패: {e}\n"
            "수동으로 설치해 주세요:\n"
            "  pip install torchvision\n"
            "또는:\n"
            "  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
        )
        sys.exit(1)

from transformers import AutoModelForCausalLM, AutoProcessor

MODEL_IDS = {
    "E4B": "google/gemma-4-E4B-it",
    "E2B": "google/gemma-4-E2B-it",
}

SYSTEM_PROMPT = """당신은 노트북 화면을 실시간으로 보면서 사용자의 목표를 달성하는 AI 에이전트입니다.
화면 이미지를 분석하고, 목표를 달성하기 위한 다음 행동 하나를 아래 JSON 형식 중 하나로만 반환하세요.
다른 텍스트는 절대 포함하지 마세요. JSON만 반환하세요.

사용 가능한 액션:
{"action":"click","x":int,"y":int,"description":"설명"}
{"action":"type","text":"입력할 텍스트","description":"설명"}
{"action":"hotkey","keys":["ctrl","c"],"description":"설명"}
{"action":"scroll","direction":"up 또는 down","amount":int,"description":"설명"}
{"action":"screenshot","description":"화면 분석만 필요할 때"}
{"action":"done","description":"목표 달성 완료 시"}

x, y 좌표는 화면 픽셀 단위입니다."""


def _detect_device() -> str:
    """사용 가능한 최적 디바이스를 반환합니다 (cuda > mps > cpu).

    환경 변수 INTELLIEYE_DEVICE로 수동 지정 가능합니다.
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
    """모델 파라미터 중 meta 디바이스에 있는 것이 있으면 True를 반환합니다."""
    for param in model.parameters():
        if param.device.type == "meta":
            return True
    return False


def _load_model(model_id: str, device: str, safe_load: bool):
    """디바이스와 안전 로드 옵션에 따라 모델을 로드합니다.

    Args:
        model_id: HuggingFace 모델 ID
        device: "cuda", "mps", 또는 "cpu"
        safe_load: True이면 meta 텐서를 방지하는 안전 옵션으로 로드

    Returns:
        로드된 모델
    """
    if device == "cuda" and not safe_load:
        return AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )

    # CPU / MPS 또는 safe_load 모드: meta 텐서를 방지하기 위해
    # device_map=None, low_cpu_mem_usage=False, float32 사용
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map=None,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=False,
    )
    model = model.to(device)
    return model


class GemmaAgent:
    """Gemma 4 E4B 또는 E2B 모델을 로드하고 화면 기반 액션을 결정합니다."""

    def __init__(self, model_name: str):
        """
        Args:
            model_name: "E4B" 또는 "E2B"
        """
        model_id = MODEL_IDS.get(model_name.upper(), MODEL_IDS["E4B"])
        print(f"  모델 로딩 중: {model_id}")
        print("  (처음 실행 시 모델 다운로드에 시간이 걸릴 수 있습니다...)")

        device = _detect_device()
        safe_load = os.environ.get("INTELLIEYE_SAFE_LOAD", "").strip() == "1"
        print(f"  디바이스: {device}" + (" (안전 로드 모드)" if safe_load or device != "cuda" else ""))

        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

        # 패드 토큰이 없으면 EOS 토큰으로 설정
        if self.processor.tokenizer.pad_token_id is None:
            self.processor.tokenizer.pad_token_id = self.processor.tokenizer.eos_token_id

        self.model = _load_model(model_id, device, safe_load)

        # meta 텐서가 감지되면 안전 로드 모드로 재시도
        if _has_meta_params(self.model):
            print(
                "  ⚠️  meta 텐서가 감지되었습니다. 안전 로드 모드로 재시도합니다..."
            )
            device = "cpu"
            self.model = _load_model(model_id, device, safe_load=True)

        # generation_config에 패드/EOS 토큰 ID 설정
        eos_id = self.processor.tokenizer.eos_token_id
        if hasattr(self.model, "generation_config"):
            if self.model.generation_config.pad_token_id is None:
                self.model.generation_config.pad_token_id = eos_id
            if self.model.generation_config.eos_token_id is None:
                self.model.generation_config.eos_token_id = eos_id

        self.device = device
        self.model_name = model_name
        print("  모델 로딩 완료!")

    def decide_action(
        self,
        screen_image: Image.Image,
        goal: str,
        history: list,
    ) -> dict:
        """
        현재 화면과 목표를 바탕으로 다음 액션을 결정합니다.

        Args:
            screen_image: 현재 화면의 PIL Image
            goal: 사용자가 요청한 목표 문자열
            history: 이전 액션 히스토리 (list of str)

        Returns:
            액션 딕셔너리
        """
        history_text = ""
        if history:
            history_text = "\n이전 수행 액션:\n" + "\n".join(
                f"  - {h}" for h in history[-5:]
            )

        user_text = (
            f"목표: {goal}{history_text}\n\n"
            "현재 화면을 분석하고 다음에 수행할 액션을 JSON으로 반환하세요."
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

        # 입력 토큰 이후의 생성 부분만 디코딩
        input_ids = inputs["input_ids"] if isinstance(inputs, dict) else inputs
        input_len = input_ids.shape[1]
        generated_ids = outputs[0][input_len:]
        response_text = self.processor.decode(generated_ids, skip_special_tokens=True).strip()

        return self._parse_json(response_text)

    def _parse_json(self, text: str) -> dict:
        """응답 텍스트에서 JSON 딕셔너리를 추출합니다."""
        # 코드 블록 제거
        text = re.sub(r"```(?:json)?", "", text).strip()

        # JSON 객체 찾기
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # 파싱 실패 시 screenshot 액션 반환
        return {"action": "screenshot", "description": f"파싱 실패 (원문: {text[:100]})"}
