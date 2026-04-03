"""Import boundary enforcement test.

Confirms that no package's source files directly import from another package's
internal submodule. The invariant is:

  packages/A/a/... must ONLY import from packages/B/b  (top-level __init__)
  not from packages/B/b/some_submodule

This test uses ast.parse to statically analyse import statements without
executing any code, so it runs even when optional dependencies are absent.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# Root of the monorepo packages directory
_REPO_ROOT = Path(__file__).parents[1]
_PACKAGES_DIR = _REPO_ROOT / "packages"

# Names of all top-level packages (the importable names, not the directory names)
# Directory layout: packages/<dir>/<pkg_name>/  (dir and pkg_name may differ by _)
_KNOWN_PACKAGES: list[str] = [
    p.name
    for pkg_dir in _PACKAGES_DIR.iterdir()
    if pkg_dir.is_dir()
    for p in [pkg_dir / pkg_dir.name]
    if p.is_dir()
]


def _collect_python_files(pkg_dir: Path) -> list[Path]:
    """Return all .py files under a package directory."""
    return sorted(pkg_dir.rglob("*.py"))


def _extract_imports(source: str) -> list[tuple[str, str]]:
    """Parse source and return (module, alias) tuples for all imports."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    imports: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, alias.asname or ""))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append((module, ""))
    return imports


def _is_cross_package_internal_import(
    importing_package: str,
    imported_module: str,
    all_packages: list[str],
) -> bool:
    """Return True if the import is a cross-package internal submodule import.

    A violation looks like:  from memory.models import X   (from inside retrieval/)
    A clean import looks like: from memory import MemoryService
    """
    parts = imported_module.split(".")
    if len(parts) < 2:
        return False  # top-level or stdlib import — fine

    top_level = parts[0]
    if top_level == importing_package:
        return False  # intra-package import — allowed

    if top_level not in all_packages:
        return False  # not one of our packages — stdlib or third-party

    # It's a cross-package import. Violation if depth > 1 (i.e., not just `pkg.X`
    # where X is re-exported from __init__, but actually going into submodules).
    # We flag imports with 2+ levels beyond top, e.g. memory.models or memory.service.
    return len(parts) >= 2


def _humanize_path(path: Path) -> str:
    try:
        return str(path.relative_to(_REPO_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Build violation list at module load time for parametrize
# ---------------------------------------------------------------------------


def _find_violations() -> list[tuple[str, str, str]]:
    """Return list of (file_path, violating_package, import_string) tuples."""
    violations: list[tuple[str, str, str]] = []

    for pkg_dir in _PACKAGES_DIR.iterdir():
        if not pkg_dir.is_dir():
            continue
        # The importable package name typically matches the directory
        pkg_name = pkg_dir.name  # e.g. "memory", "context_assembler"
        inner_dir = pkg_dir / pkg_name
        if not inner_dir.is_dir():
            continue

        for py_file in _collect_python_files(inner_dir):
            if py_file.name.startswith("test_"):
                continue  # skip test files inside packages (they may import internals)
            try:
                source = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            for mod, _ in _extract_imports(source):
                if _is_cross_package_internal_import(pkg_name, mod, _KNOWN_PACKAGES):
                    # Check if it's a depth>1 access (real internal submodule cross-import)
                    parts = mod.split(".")
                    if len(parts) >= 3:  # e.g. memory.models.something — deep violation
                        violations.append((_humanize_path(py_file), pkg_name, mod))
                    elif len(parts) == 2:
                        # e.g. "memory.models" or "memory.service" — these are internal
                        # submodule imports; flag unless the second part is a known
                        # re-exported name. We accept "pkg.ClassName" but not "pkg.submodule".
                        sub = parts[1]
                        # Heuristic: submodule names are lowercase snake_case module files.
                        # Re-exported class names are PascalCase. Flag only snake_case subs.
                        if sub[0].islower() and "_" in sub or (sub[0].islower() and len(sub) > 5):
                            violations.append((_humanize_path(py_file), pkg_name, mod))

    return violations


_VIOLATIONS = _find_violations()


class TestImportBoundaries:
    def test_no_known_packages_exist(self):
        """Sanity: the packages directory must contain at least 5 packages."""
        assert len(_KNOWN_PACKAGES) >= 5, f"Expected at least 5 packages, found: {_KNOWN_PACKAGES}"

    @pytest.mark.parametrize(
        "violation",
        _VIOLATIONS,
        ids=[f"{v[0]}::{v[2]}" for v in _VIOLATIONS] if _VIOLATIONS else ["no_violations"],
    )
    def test_no_cross_package_internal_imports(self, violation):
        """Each parametrized case is a detected boundary violation."""
        file_path, importing_pkg, imported_module = violation
        pytest.fail(
            f"Boundary violation in {file_path!r}:\n"
            f"  Package '{importing_pkg}' imports internal submodule '{imported_module}'.\n"
            f"  Only top-level imports from other packages are allowed."
        )

    def test_boundary_violations_count(self):
        """Count of boundary violations must be zero."""
        if _VIOLATIONS:
            details = "\n".join(f"  {f}: {m}" for f, _, m in _VIOLATIONS)
            pytest.fail(f"Found {len(_VIOLATIONS)} cross-package internal import(s):\n{details}")
