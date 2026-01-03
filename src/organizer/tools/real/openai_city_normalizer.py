from __future__ import annotations

import os
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OpenAICityNormalizerTool:
    """
    Zamienia polską nazwę miasta (w dowolnej odmianie) na mianownik.
    Wymaga: OPENAI_API_KEY.
    """
    name: str = "openai_city_normalizer"
    model: str = "gpt-4o-mini"

    def __call__(self, *, text: str) -> dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing env var: OPENAI_API_KEY")

        # lazy import
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        resp = client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Zamieniasz polskie nazwy miast/miejsc na mianownik. "
                        "Odpowiadaj wyłącznie JSON-em."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Wejście: {text}\n"
                        'Zwróć dokładnie: {"nominative": "<mianownik>"}'
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )

        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        nominative = str(data.get("nominative", text)).strip()
        return {"input": text, "nominative": nominative, "source": "openai"}
