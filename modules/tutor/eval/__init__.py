"""
Evaluation harness for the Socratic Tutor (``sage-tutor``).

Runs scripted student conversations (``conversations/*.json``) through the
full SAGE turn loop and reports rule violations, answer leaks (LLM judge),
citations, stage coverage and latency against the PRD success criteria.

Usage: ``python -m modules.tutor.eval --help``
"""
