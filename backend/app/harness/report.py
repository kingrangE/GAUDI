"""Write harness results to a JSON blob + a human-readable markdown summary."""

import json
from pathlib import Path
from typing import Any


def _render_markdown(results: dict[str, Any], title: str) -> str:
    lines = [f"# Judge reliability report — {title}", ""]
    for section, payload in results.items():
        lines.append(f"## {section}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(payload, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def write_report(
    results: dict[str, Any], out_dir: str, name: str, stamp: str
) -> tuple[Path, Path]:
    """Write ``<name>_<stamp>.json`` and ``.md`` into ``out_dir``; return both paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    base = f"{name}_{stamp}"
    json_path = out / f"{base}.json"
    md_path = out / f"{base}.md"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(results, base), encoding="utf-8")
    return json_path, md_path
