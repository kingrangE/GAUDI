"""Offline judge-reliability harness (developer/debugging tool).

NOT part of the live request path and has no UI. It evaluates the LLM-as-a-judge
itself — consistency, human agreement, self-preference bias, position bias — so
the judge's prompt/structure can be iterated with evidence. Reusable across
features and models via the ``JudgeAdapter`` interface; test_design is the first
adapter. Run via ``python -m app.harness.runner``.
"""
