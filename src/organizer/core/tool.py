from __future__ import annotations

from typing import Any, Protocol


class Tool(Protocol):
    """
    Minimalny kontrakt na narzędzie (np. API).
    Narzędzie jest wywoływalne i zwraca dane (payload).
    """
    name: str

    def __call__(self, **kwargs: Any) -> Any:
        ...
