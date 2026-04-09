"""
model.py — IntelliEye
Gemma 4 E4B / E2B 모델 래퍼
Made by Hyunho Cho
"""

import json
import re
import subprocess
import sys

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

        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
        )
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
        inputs = inputs.to(self.model.device)

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
