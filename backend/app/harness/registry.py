"""Registry of harness targets so the offline reliability runner is feature-agnostic.

The analyses (consistency / agreement / position-bias / self-preference) depend only on the
``JudgeAdapter`` protocol, so a feature becomes harness-pluggable by registering an adapter
factory + the directory holding its standard fixture set. ``runner`` looks targets up by name.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.harness.interface import JudgeAdapter


@dataclass(frozen=True)
class HarnessTarget:
    """How to drive the harness for one feature."""

    name: str
    make_adapter: Callable[[str | None], JudgeAdapter]  # model pin (or None) -> adapter
    fixtures_dir: Path
    # Optional custom inputs shaper for features whose judge doesn't fit the standard fixture
    # set (e.g. a per-problem classifier). When None, the runner shapes the standard fixtures.
    build_inputs: Callable[[], dict] | None = None


_REGISTRY: dict[str, HarnessTarget] = {}


def register_target(target: HarnessTarget) -> None:
    """Register (or replace) a harness target by name."""

    _REGISTRY[target.name] = target


def get_target(name: str) -> HarnessTarget:
    """Look up a registered target, or raise with the available names."""

    if name not in _REGISTRY:
        raise KeyError(f"no harness target registered for {name!r}; have {list_targets()}")
    return _REGISTRY[name]


def list_targets() -> list[str]:
    """Names of all registered targets, sorted."""

    return sorted(_REGISTRY)
