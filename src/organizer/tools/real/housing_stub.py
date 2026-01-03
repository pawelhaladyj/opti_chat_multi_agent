from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RealHousingToolStub:
    """
    Placeholder na przyszłe integracje z noclegami.
    Tu celowo nie ma realnego providera.

    Zwraca czytelny błąd, żeby nie udawać, że działa.
    """
    name: str = "real_housing_stub"

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError(
            "Real housing integration is provider-specific. "
            "Use FakeHousingAPI for now or implement an adapter for your chosen provider."
        )
