"""
Socratic Tutor Agent (Tahir) — ``sage-tutor``.

Generates the pedagogical reply for the scaffolding stage chosen by the
orchestrator.  Plugs into the backend through ``BaseSocraticTutor``.

Reference: docs/TEAM_MODULE_DIVISION.md §2.4 & §3.3
"""

from modules.tutor.agent import SocraticTutor

__all__ = ["SocraticTutor"]
