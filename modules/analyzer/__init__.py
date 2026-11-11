"""
Student Understanding Analyzer (Nidhi) — ``sage-analyzer``.

Two ways in:

* ``UnderstandingAnalyzer`` — async class implementing
  ``backend.services.interfaces.BaseUnderstandingAnalyzer``.
* ``analyze(dict) -> dict`` — the sync function ``backend/services/adapters.py``
  imports (``from modules.analyzer import analyze``) when
  ``USE_MOCK_ANALYZER=false``.

Reference: docs/TEAM_MODULE_DIVISION.md §2.3 & §3.1.
"""

from __future__ import annotations

from typing import Any

from backend.schemas.contracts import AnalyzerInput

from modules.analyzer.analyzer import UnderstandingAnalyzer

_default = UnderstandingAnalyzer()


def analyze(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate an ``AnalyzerInput`` dict and return an ``AnalyzerOutput`` dict."""
    result = _default.analyze_sync(AnalyzerInput.model_validate(payload))
    return result.model_dump(mode="json")


__all__ = ["UnderstandingAnalyzer", "analyze"]
