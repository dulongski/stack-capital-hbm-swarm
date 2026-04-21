from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass
class LLMResult:
    content: str
    model: str
    estimated_prompt_tokens: int
    estimated_completion_tokens: int
    estimated_cost_usd: float
    used_remote: bool


class OpenRouterClient:
    def __init__(self, api_key: str | None, model: str, budget_usd: float) -> None:
        self.api_key = api_key
        self.model = model
        self.budget_usd = budget_usd
        self.estimated_spend_usd = 0.0

    @staticmethod
    def estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    def complete_json(self, system_prompt: str, user_prompt: str, *, force_offline: bool = False) -> LLMResult:
        prompt_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_prompt)
        if force_offline or not self.api_key:
            return LLMResult(
                content="{}",
                model="offline-deterministic",
                estimated_prompt_tokens=prompt_tokens,
                estimated_completion_tokens=1,
                estimated_cost_usd=0.0,
                used_remote=False,
            )

        if self.estimated_spend_usd >= self.budget_usd:
            raise RuntimeError("OpenRouter budget guard reached")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/dulongski/stack-capital-hbm-swarm",
                "X-Title": "Stack HBM Swarm",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenRouter request failed: {exc}") from exc

        content = data["choices"][0]["message"]["content"]
        completion_tokens = self.estimate_tokens(content)
        estimated_cost = (prompt_tokens + completion_tokens) * 0.0000005
        self.estimated_spend_usd += estimated_cost
        return LLMResult(
            content=content,
            model=self.model,
            estimated_prompt_tokens=prompt_tokens,
            estimated_completion_tokens=completion_tokens,
            estimated_cost_usd=estimated_cost,
            used_remote=True,
        )

