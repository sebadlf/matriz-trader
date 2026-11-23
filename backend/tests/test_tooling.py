"""AC-6, AC-13, AC-14: librerías internas importables y regla ANN de Ruff sin excepciones."""

import importlib
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("module", ["market_data_client", "matriz_client"])
def test_internal_libraries_are_importable(module: str) -> None:
    importlib.import_module(module)


def _ruff_lint_config() -> dict[str, Any]:
    pyproject = tomllib.loads((BACKEND_DIR / "pyproject.toml").read_text(encoding="utf-8"))
    lint: dict[str, Any] = pyproject["tool"]["ruff"]["lint"]
    return lint


def test_ann_rules_enabled_without_exceptions() -> None:
    lint = _ruff_lint_config()

    assert "ANN" in lint["select"]
    ignored: list[str] = [*lint.get("ignore", []), *lint.get("extend-ignore", [])]
    for rules in lint.get("per-file-ignores", {}).values():
        ignored.extend(rules)
    for rules in lint.get("extend-per-file-ignores", {}).values():
        ignored.extend(rules)
    assert not [rule for rule in ignored if rule.startswith("ANN")]


def test_ruff_reports_missing_annotations() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--no-cache", "--stdin-filename", "probe.py", "-"],
        cwd=BACKEND_DIR,
        input="def f(x):\n    return x\n",
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode != 0
    assert "ANN001" in result.stdout
    assert "ANN201" in result.stdout
