#!/usr/bin/env python3
"""Auditoría de vulnerabilidades de dependencias (AC-43). Lo corre el job `security` de CI.

- Python: `uv export --frozen` (sin las fuentes git privadas de market-libs, que no están en PyPI
  ni en OSV) → `pip-audit` (fijado en PIP_AUDIT).
- Node: `osv-scanner` sobre `frontend/pnpm-lock.yaml`.

Cada hallazgo se filtra contra `security-allowlist.toml`. Sale con 1 si queda algún hallazgo no
permitido, si alguna entrada de la allowlist venció o es inválida, o si falta una herramienta;
con 0 en otro caso. Solo usa la stdlib.

Uso: python3 scripts/audit.py [--allowlist RUTA]
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# tomllib existe desde Python 3.11. Si el python3 del sistema es más viejo, se re-ejecuta con uv.
if sys.version_info < (3, 11):  # noqa: UP036
    if shutil.which("uv") is None:
        sys.exit("scripts/audit.py requiere Python >= 3.11 (o `uv` para obtenerlo).")
    os.execvp(  # noqa: S606
        "uv",
        ["uv", "run", "--no-project", "--python", ">=3.11", "python", __file__, *sys.argv[1:]],
    )

import argparse
import json
import re
import subprocess
import tempfile
import tomllib
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parent.parent
DEFAULT_ALLOWLIST: Final = ROOT / "security-allowlist.toml"
PIP_AUDIT: Final = "pip-audit@2.10.1"  # Critical Decision T1: `uv audit` sigue experimental
PRIVATE_PACKAGES: Final = ("market-data-client", "matriz-client")
ECOSYSTEMS: Final = {"PyPI", "npm"}
REQUIRED_KEYS: Final = ("id", "ecosystem", "package", "reason", "expires")


class AuditError(Exception):
    """Falla de entorno o de herramienta: no se pudo auditar."""


@dataclass(frozen=True)
class Finding:
    ecosystem: str
    package: str
    version: str
    id: str
    aliases: frozenset[str] = field(default_factory=frozenset)
    fix_versions: tuple[str, ...] = ()

    def line(self) -> str:
        fixes = ",".join(self.fix_versions) or "-"
        return f"{self.ecosystem} {self.package} {self.version} {self.id} {fixes}"


@dataclass(frozen=True)
class AllowEntry:
    id: str
    ecosystem: str
    package: str
    reason: str
    expires: date


def normalize(ecosystem: str, package: str) -> str:
    if ecosystem == "PyPI":  # PEP 503
        return re.sub(r"[-_.]+", "-", package).lower()
    return package


def require(tool: str) -> None:
    if shutil.which(tool) is None:
        raise AuditError(f"Falta `{tool}` en el PATH (ver README «Calidad y tests»).")


def run_json(cmd: list[str], cwd: Path, ok_codes: set[int]) -> Any:  # noqa: ANN401
    """Corre `cmd` y devuelve su stdout como JSON. Falla si el exit code no es esperado."""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)  # noqa: S603
    if proc.returncode not in ok_codes:
        raise AuditError(f"`{' '.join(cmd)}` salió con {proc.returncode}:\n{proc.stderr.strip()}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AuditError(f"`{cmd[0]}` no devolvió JSON válido:\n{proc.stderr.strip()}") from exc


def audit_python() -> list[Finding]:
    require("uv")
    backend = ROOT / "backend"
    with tempfile.TemporaryDirectory() as tmp:
        reqs = Path(tmp) / "requirements.txt"
        export = ["uv", "export", "--frozen", "--no-hashes", "--quiet", "--output-file", str(reqs)]
        for pkg in PRIVATE_PACKAGES:
            export += ["--no-emit-package", pkg]
        proc = subprocess.run(export, cwd=backend, capture_output=True, text=True, check=False)  # noqa: S603
        if proc.returncode != 0:
            raise AuditError(f"`uv export` salió con {proc.returncode}:\n{proc.stderr.strip()}")
        cmd = ["uvx", PIP_AUDIT, "--strict", "--disable-pip", "--no-deps", "-r", str(reqs), "-f", "json"]
        # pip-audit sale con 1 cuando encuentra vulnerabilidades; el JSON las trae igual.
        report = run_json(cmd, backend, ok_codes={0, 1})
    findings = [
        Finding(
            ecosystem="PyPI",
            package=dep["name"],
            version=dep.get("version", "?"),
            id=vuln["id"],
            aliases=frozenset(vuln.get("aliases", [])),
            fix_versions=tuple(vuln.get("fix_versions", [])),
        )
        for dep in report.get("dependencies", [])
        for vuln in dep.get("vulns", [])
    ]
    skipped = [d for d in report.get("dependencies", []) if "skip_reason" in d]
    if skipped:
        names = ", ".join(f"{d['name']} ({d['skip_reason']})" for d in skipped)
        raise AuditError(f"pip-audit no pudo auditar: {names}")
    return findings


def osv_fix_versions(vuln: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                event["fixed"]
                for affected in vuln.get("affected", [])
                for rng in affected.get("ranges", [])
                for event in rng.get("events", [])
                if "fixed" in event
            }
        )
    )


def audit_node() -> list[Finding]:
    require("osv-scanner")
    lockfile = ROOT / "frontend" / "pnpm-lock.yaml"
    cmd = ["osv-scanner", "scan", "source", "--lockfile", str(lockfile), "--format", "json"]
    # 0 = sin hallazgos, 1 = hallazgos (vienen en el JSON). Cualquier otro código es una falla.
    report = run_json(cmd, ROOT, ok_codes={0, 1})
    return [
        Finding(
            ecosystem="npm",
            package=pkg["package"]["name"],
            version=pkg["package"].get("version", "?"),
            id=vuln["id"],
            aliases=frozenset(vuln.get("aliases", [])),
            fix_versions=osv_fix_versions(vuln),
        )
        for result in report.get("results") or []
        for pkg in result.get("packages") or []
        for vuln in pkg.get("vulnerabilities") or []
    ]


def load_allowlist(path: Path) -> tuple[list[AllowEntry], list[str]]:
    """Devuelve las entradas válidas y los errores (entradas inválidas)."""
    if not path.exists():
        raise AuditError(f"No existe la allowlist {path}")
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    entries: list[AllowEntry] = []
    errors: list[str] = []
    for i, raw in enumerate(data.get("ignore", []), start=1):
        missing = [k for k in REQUIRED_KEYS if not raw.get(k)]
        if missing:
            errors.append(f"allowlist: la entrada #{i} no tiene {', '.join(missing)}")
            continue
        if raw["ecosystem"] not in ECOSYSTEMS:
            errors.append(f"allowlist: la entrada #{i} ({raw['id']}) tiene ecosystem inválido «{raw['ecosystem']}»")
            continue
        if not isinstance(raw["expires"], date) or isinstance(raw["expires"], datetime):
            errors.append(f"allowlist: la entrada #{i} ({raw['id']}) necesita `expires` como fecha TOML (AAAA-MM-DD)")
            continue
        entries.append(AllowEntry(**{k: raw[k] for k in REQUIRED_KEYS}))
    return entries, errors


def is_allowed(finding: Finding, entries: list[AllowEntry]) -> bool:
    ids = {finding.id, *finding.aliases}
    pkg = normalize(finding.ecosystem, finding.package)
    return any(
        e.ecosystem == finding.ecosystem and normalize(e.ecosystem, e.package) == pkg and e.id in ids
        for e in entries
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    args = parser.parse_args()

    try:
        entries, problems = load_allowlist(args.allowlist)
        today = datetime.now(UTC).date()
        expired = [e for e in entries if e.expires < today]
        problems += [
            f"allowlist vencida: {e.ecosystem} {e.package} {e.id} (expires {e.expires.isoformat()})" for e in expired
        ]
        active = [e for e in entries if e.expires >= today]
        findings = audit_python() + audit_node()
    except AuditError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    blocked = [f for f in findings if not is_allowed(f, active)]
    for f in blocked:
        print(f.line())
    for p in problems:
        print(p)

    allowed = len(findings) - len(blocked)
    print(
        f"\nAuditoría: {len(findings)} hallazgo(s), {allowed} permitido(s) por la allowlist, "
        f"{len(blocked)} bloqueante(s), {len(problems)} problema(s) en la allowlist.",
        file=sys.stderr,
    )
    return 1 if blocked or problems else 0


if __name__ == "__main__":
    sys.exit(main())
