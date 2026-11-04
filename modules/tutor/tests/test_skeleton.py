"""
Smoke tests for the Socratic Tutor package wiring.

Verifies the package imports from the repo root and that ``SocraticTutor``
satisfies the orchestrator's ``BaseSocraticTutor`` interface.
"""

import inspect

from backend.services.interfaces import BaseSocraticTutor
from modules.tutor import SocraticTutor


def test_tutor_implements_interface() -> None:
    """SocraticTutor is a concrete BaseSocraticTutor the orchestrator can instantiate."""
    tutor = SocraticTutor()
    assert isinstance(tutor, BaseSocraticTutor)


def test_respond_is_async() -> None:
    """respond() must be awaitable, matching the async interface."""
    assert inspect.iscoroutinefunction(SocraticTutor.respond)
