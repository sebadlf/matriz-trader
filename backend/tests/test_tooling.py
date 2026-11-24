"""Guardas de tooling: libs internas, reglas de Ruff, contratos de import-linter y cobertura.

AC-6, AC-13, AC-14 (spec base) y AC-20, AC-23, AC-25, AC-33 (guardas de calidad).
"""

import importlib
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Final

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]

REQUIRED_RUFF_GROUPS: Final = {
    "ASYNC", "FAST", "S", "DTZ", "BLE", "TRY", "T20", "ERA", "PT", "PIE", "RET", "C4",
    "PTH", "LOG", "G", "PERF", "TC", "ARG", "FURB", "TID", "PL", "C90", "FBT",
}  # fmt: skip
REQUIRED_CONTRACTS: Final = {"Capas", "Dominio puro", "API sin acceso directo a la DB"}
MIN_COVERAGE: Final = 85


def _pyproject() -> dict[str, Any]:
    return tomllib.loads((BACKEND_DIR / "pyproject.toml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("module", ["market_data_client", "matriz_client"])
def test_internal_libraries_are_importable(module: str) -> None:
    importlib.import_module(module)


def _ruff_lint_config() -> dict[str, Any]:
    lint: dict[str, Any] = _pyproject()["tool"]["ruff"]["lint"]
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


def test_ruff_groups_enabled() -> None:
    lint = _ruff_lint_config()
    enabled = {*lint["select"], *lint.get("extend-select", [])}

    assert REQUIRED_RUFF_GROUPS - enabled == set()


def test_ruff_ignores_are_justified() -> None:
    lint = _ruff_lint_config()
    ignored: list[str] = lint.get("ignore", [])
    lines = (BACKEND_DIR / "pyproject.toml").read_text(encoding="utf-8").splitlines()

    for rule in ignored:
        entries = [line for line in lines if line.strip().startswith(f'"{rule}"')]
        assert entries, f"{rule}: no aparece como entrada de `ignore`"
        _, _, comment = entries[0].partition("#")
        assert comment.strip(), f"{rule}: la excepción no tiene comentario que la justifique"


def test_import_contracts_present() -> None:
    contracts: list[dict[str, Any]] = _pyproject()["tool"]["importlinter"]["contracts"]

    assert REQUIRED_CONTRACTS - {contract["name"] for contract in contracts} == set()


def test_coverage_threshold() -> None:
    coverage: dict[str, Any] = _pyproject()["tool"]["coverage"]

    assert coverage["report"]["fail_under"] >= MIN_COVERAGE
    assert coverage["run"]["branch"] is True
