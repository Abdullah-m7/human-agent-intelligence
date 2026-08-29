"""OpenAI-compatible synthesis client and frozen Stage-005 prompt contract."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Optional, Sequence
from urllib import error, request


BUDGETS = (1, 2, 4, 8)
BASE_SEED = 505_000
TEMPERATURE = 0.8
TOP_P = 0.95
MAX_TOKENS = 1536

SYSTEM_PROMPT = (
    "STRICT OUTPUT CONTRACT: synthesize deterministic Python programs for ARC grid transformations. "
    "Return only Python source beginning with def solve(grid): and returning a rectangular "
    "list of lists of integer colors 0-9. Do not import modules. Do not use files, "
    "network, subprocesses, eval, exec, reflection, or external state. Use only basic "
    "Python control flow, comprehensions, and safe builtins. Infer a general rule from "
    "all visible training pairs; never hard-code the target output. Return a complete compact "
    "program; avoid Markdown, explanations, tests, docstrings, and comments, and keep the "
    "implementation under 60 physical lines when possible."
)

USER_TEMPLATE = (
    "VISIBLE_TRAINING_PAIRS={training}\n"
    "TARGET_INPUT={target}\n"
    "Synthesize one complete candidate program now."
)

RESPONSE_CONTRACT = "raw_python_source_with_fence_tolerance_v1"


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def seed_for_candidate(candidate_index: int) -> int:
    if candidate_index < 1:
        raise ValueError("candidate_index is one-based and must be positive")
    return BASE_SEED + candidate_index


def user_prompt(training: Sequence[dict[str, Any]], target_input: list[list[int]]) -> str:
    return USER_TEMPLATE.format(training=canonical_json(list(training)), target=canonical_json(target_input))


def request_body(
    model: str,
    training: Sequence[dict[str, Any]],
    target_input: list[list[int]],
    seed: int,
) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt(training, target_input)},
        ],
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "seed": seed,
        "max_tokens": MAX_TOKENS,
    }


def contract_hashes() -> dict[str, str]:
    return {
        "system_prompt_sha256": sha256_bytes(SYSTEM_PROMPT.encode("utf-8")),
        "user_template_sha256": sha256_bytes(USER_TEMPLATE.encode("utf-8")),
        "response_contract_sha256": sha256_bytes(RESPONSE_CONTRACT.encode("utf-8")),
    }


@dataclass(frozen=True)
class ModelCall:
    content: str
    content_sha256: str
    request_sha256: str
    latency_s: float
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    finish_reason: Optional[str]


class OpenAICompatSynthesisClient:
    def __init__(self, base_url: str, model: str, timeout_s: int = 600):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def server_context_size(self) -> int:
        req = request.Request(self.base_url + "/props", method="GET")
        with request.urlopen(req, timeout=30) as response:
            obj = json.loads(response.read().decode("utf-8"))
        return int(obj["default_generation_settings"]["n_ctx"])

    def infer(
        self,
        training: Sequence[dict[str, Any]],
        target_input: list[list[int]],
        seed: int,
    ) -> ModelCall:
        body = request_body(self.model, training, target_input, seed)
        payload = canonical_json(body).encode("utf-8")
        req = request.Request(
            self.base_url + "/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.monotonic()
        try:
            with request.urlopen(req, timeout=self.timeout_s) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        choice = decoded["choices"][0]
        content = choice["message"].get("content", "") or ""
        usage = decoded.get("usage", {})
        return ModelCall(
            content=content,
            content_sha256=sha256_bytes(content.encode("utf-8")),
            request_sha256=sha256_bytes(payload),
            latency_s=round(time.monotonic() - started, 6),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            finish_reason=choice.get("finish_reason"),
        )
