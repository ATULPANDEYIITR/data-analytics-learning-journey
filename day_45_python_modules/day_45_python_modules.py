"""
Python Modules, Imports, Packages, Standard Library, Virtual Environments,
and Dependency Management

A self-contained executable learning program that progresses from basic imports
to package discovery, import mechanics, virtual-environment inspection,
dependency metadata, reproducibility, and a small dependency-aware application.

The examples use only the Python standard library.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from types import ModuleType
from typing import Iterable


# ---------------------------------------------------------------------------
# Fundamental imports
# ---------------------------------------------------------------------------

def demonstrate_basic_imports() -> None:
    """Show several standard-library modules and the distinction between them."""

    import math
    import statistics
    from datetime import datetime, timezone

    values = [12, 18, 21, 27, 32]

    print("\n=== Basic Imports ===")
    print("math.sqrt(81):", math.sqrt(81))
    print("statistics.mean(values):", statistics.mean(values))
    print("Current UTC year:", datetime.now(timezone.utc).year)

    # Importing a module does not copy its functions into the current namespace.
    # The module name remains the namespace used to access its members.
    print("math module object:", math)


def demonstrate_import_styles() -> None:
    """Compare module import, from-import, and aliases."""

    import statistics as stats
    from pathlib import Path as FilePath

    values = [4, 8, 15, 16, 23, 42]

    print("\n=== Import Styles ===")
    print("Module alias:", stats.median(values))
    print("Imported name alias:", FilePath.cwd())

    # Wildcard imports are intentionally avoided because they obscure where
    # names came from and can overwrite existing names.
    print("Explicit imports keep dependencies visible.")


# ---------------------------------------------------------------------------
# Module objects and import discovery
# ---------------------------------------------------------------------------

def inspect_module(module_name: str) -> None:
    """Load an already-installed module and inspect useful module metadata."""

    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        print(f"Could not import {module_name!r}: {exc}")
        return

    print(f"\n=== Module Inspection: {module_name} ===")
    print("Type:", type(module).__name__)
    print("Module name:", module.__name__)
    print("Module file:", getattr(module, "__file__", "<built-in>"))
    print("Package:", getattr(module, "__package__", ""))
    print("Loader:", getattr(module, "__loader__", None).__class__.__name__)

    public_names = [name for name in dir(module) if not name.startswith("_")]
    print("Sample public names:", public_names[:10])


def demonstrate_importlib() -> None:
    """Demonstrate dynamic imports and checking whether a module is available."""

    print("\n=== Dynamic Import and Discovery ===")

    candidates = ["json", "pathlib", "statistics", "this_module_does_not_exist"]

    for name in candidates:
        spec = importlib.util.find_spec(name)
        print(f"{name:32} available={spec is not None}")

    # Dynamic import is useful when a feature is optional or selected at runtime.
    module = importlib.import_module("json")
    print("Dynamic JSON module:", module.dumps({"loaded": True}))


# ---------------------------------------------------------------------------
# Packages and package-style structure
# ---------------------------------------------------------------------------

def create_demo_package(root: Path) -> Path:
    """
    Create a temporary package with multiple modules.

    This demonstrates the filesystem relationship between a package and its
    modules without requiring installation of an external package.
    """

    package_dir = root / "repository_tools"
    package_dir.mkdir()

    (package_dir / "__init__.py").write_text(
        '"""Small package used for import demonstrations."""\n'
        '__version__ = "1.0.0"\n',
        encoding="utf-8",
    )

    (package_dir / "validation.py").write_text(
        """
def valid_repository_name(name: str) -> bool:
    return bool(name) and all(
        character.isalnum() or character in "-_"
        for character in name
    )
""".strip()
        + "\n",
        encoding="utf-8",
    )

    (package_dir / "repository.py").write_text(
        """
from .validation import valid_repository_name

class Repository:
    def __init__(self, name: str):
        if not valid_repository_name(name):
            raise ValueError("Invalid repository name")
        self.name = name

    def full_name(self, owner: str) -> str:
        return f"{owner}/{self.name}"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    return package_dir


def demonstrate_local_package() -> None:
    """Import a package and a sibling module using a temporary import path."""

    print("\n=== Local Package ===")

    with tempfile.TemporaryDirectory(prefix="python_package_demo_") as directory:
        root = Path(directory)
        create_demo_package(root)

        # Python searches sys.path when resolving imports. Adding the temporary
        # project directory makes repository_tools importable for this demo.
        sys.path.insert(0, str(root))

        try:
            package = importlib.import_module("repository_tools")
            repository_module = importlib.import_module(
                "repository_tools.repository"
            )

            repository = repository_module.Repository("release-tools")

            print("Package version:", package.__version__)
            print("Repository:", repository.full_name("engineering"))
        finally:
            # Removing temporary paths prevents accidental import resolution
            # from a directory that no longer exists.
            if str(root) in sys.path:
                sys.path.remove(str(root))

            for name in list(sys.modules):
                if name == "repository_tools" or name.startswith("repository_tools."):
                    del sys.modules[name]


# ---------------------------------------------------------------------------
# Standard library: filesystem, configuration, serialization, hashing
# ---------------------------------------------------------------------------

def demonstrate_standard_library() -> None:
    """Combine several standard-library modules in a realistic task."""

    import hashlib
    import configparser

    print("\n=== Standard Library Workflow ===")

    configuration = configparser.ConfigParser()
    configuration["application"] = {
        "name": "deployment-auditor",
        "environment": "development",
        "timeout_seconds": "15",
    }

    with tempfile.TemporaryDirectory(prefix="stdlib_demo_") as directory:
        root = Path(directory)
        config_file = root / "application.ini"
        manifest_file = root / "manifest.json"

        with config_file.open("w", encoding="utf-8") as handle:
            configuration.write(handle)

        manifest = {
            "application": configuration["application"]["name"],
            "environment": configuration["application"]["environment"],
            "configuration": config_file.name,
        }

        manifest_file.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        digest = hashlib.sha256(manifest_file.read_bytes()).hexdigest()

        print("Configuration:", config_file.read_text(encoding="utf-8").strip())
        print("Manifest:", manifest_file.read_text(encoding="utf-8").strip())
        print("SHA-256:", digest)


# ---------------------------------------------------------------------------
# Dependency metadata and version constraints
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Dependency:
    """A minimal representation of a declared application dependency."""

    name: str
    minimum_version: str
    reason: str


def parse_version(version: str) -> tuple[int, ...]:
    """Parse simple numeric versions such as 3.13.0."""

    if not re.fullmatch(r"\d+(?:\.\d+)*", version):
        raise ValueError(f"Unsupported version format: {version!r}")

    return tuple(int(part) for part in version.split("."))


def version_at_least(actual: str, minimum: str) -> bool:
    """Compare normalized numeric versions without external packages."""

    actual_parts = parse_version(actual)
    minimum_parts = parse_version(minimum)

    width = max(len(actual_parts), len(minimum_parts))
    actual_parts += (0,) * (width - len(actual_parts))
    minimum_parts += (0,) * (width - len(minimum_parts))

    return actual_parts >= minimum_parts


def demonstrate_dependency_model() -> None:
    """Represent dependency declarations and evaluate a Python requirement."""

    print("\n=== Dependency Metadata ===")

    dependencies = [
        Dependency(
            name="Python",
            minimum_version="3.11",
            reason="Required for the application's supported runtime.",
        ),
        Dependency(
            name="pip",
            minimum_version="23.0",
            reason="Used to install and resolve project dependencies.",
        ),
    ]

    current_python = platform.python_version()

    for dependency in dependencies:
        if dependency.name == "Python":
            satisfied = version_at_least(current_python, dependency.minimum_version)
            print(
                f"{dependency.name} >= {dependency.minimum_version}: "
                f"{satisfied} ({current_python})"
            )

        print("Reason:", dependency.reason)

    serialized = json.dumps([asdict(item) for item in dependencies], indent=2)
    print("Dependency metadata:")
    print(serialized)


# ---------------------------------------------------------------------------
# Virtual-environment inspection
# ---------------------------------------------------------------------------

def virtual_environment_state() -> dict[str, object]:
    """Inspect whether the current interpreter appears to run in a venv."""

    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    in_virtual_environment = sys.prefix != base_prefix

    return {
        "active": in_virtual_environment,
        "sys.prefix": sys.prefix,
        "sys.base_prefix": base_prefix,
        "python_executable": sys.executable,
        "site_packages_hint": str(Path(sys.prefix) / "Lib" / "site-packages"),
    }


def demonstrate_virtual_environment() -> None:
    """Explain the observable interpreter properties of a virtual environment."""

    print("\n=== Virtual Environment ===")

    state = virtual_environment_state()

    for key, value in state.items():
        print(f"{key}: {value}")

    if state["active"]:
        print("The current process is using an isolated virtual environment.")
    else:
        print(
            "The current process does not appear to be inside a virtual "
            "environment."
        )


# ---------------------------------------------------------------------------
# Dependency-management commands
# ---------------------------------------------------------------------------

def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command safely and return captured output."""

    try:
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return subprocess.CompletedProcess(
            command,
            returncode=127,
            stdout="",
            stderr=str(exc),
        )


def demonstrate_package_manager() -> None:
    """
    Inspect pip without modifying the user's environment.

    The demonstration deliberately uses read-only commands such as
    `pip --version` and `pip list`; it never silently installs packages.
    """

    print("\n=== Dependency Manager Inspection ===")

    pip_path = shutil.which("pip")

    if pip_path is None:
        print("pip executable was not found on PATH.")
        print("The current Python interpreter may still provide pip via -m pip.")
        return

    result = run_command([sys.executable, "-m", "pip", "--version"])

    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print("Unable to query pip:")
        print(result.stderr.strip())

    list_result = run_command(
        [sys.executable, "-m", "pip", "list", "--format=json"]
    )

    if list_result.returncode == 0:
        try:
            packages = json.loads(list_result.stdout)
            print("Installed package count:", len(packages))
            print("First installed packages:", packages[:5])
        except json.JSONDecodeError:
            print("pip returned unexpected package metadata.")
    else:
        print("Unable to inspect installed packages.")


# ---------------------------------------------------------------------------
# Requirements and reproducibility
# ---------------------------------------------------------------------------

def validate_requirement_line(line: str) -> bool:
    """
    Validate a conservative requirements-style dependency declaration.

    Supported examples:
        requests
        requests==2.32.5
        requests>=2.31
        requests>=2.31,<3
    """

    pattern = re.compile(
        r"^[A-Za-z0-9_.-]+"
        r"(?:"
        r"==\s*\d+(?:\.\d+)*"
        r"|>=\s*\d+(?:\.\d+)*"
        r"(?:\s*,\s*<\s*\d+(?:\.\d+)*)?"
        r")?$"
    )

    return bool(pattern.fullmatch(line.strip()))


def demonstrate_dependency_file() -> None:
    """Create and validate a small requirements.txt representation."""

    print("\n=== Dependency Declaration ===")

    requirements = [
        "httpx>=0.27,<1",
        "pydantic>=2.0,<3",
        "deployment-auditor==1.4.0",
    ]

    for requirement in requirements:
        print(requirement, "->", validate_requirement_line(requirement))

    invalid = "httpx=>broken"
    print(invalid, "->", validate_requirement_line(invalid))

    with tempfile.TemporaryDirectory(prefix="requirements_demo_") as directory:
        requirements_file = Path(directory) / "requirements.txt"
        requirements_file.write_text(
            "\n".join(requirements) + "\n",
            encoding="utf-8",
        )

        print("Created:", requirements_file)
        print(requirements_file.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Dependency conflict model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VersionConstraint:
    package: str
    minimum: tuple[int, ...] | None = None
    maximum_exclusive: tuple[int, ...] | None = None

    def accepts(self, version: str) -> bool:
        candidate = parse_version(version)

        if self.minimum is not None:
            width = max(len(candidate), len(self.minimum))
            candidate_padded = candidate + (0,) * (width - len(candidate))
            minimum_padded = self.minimum + (0,) * (width - len(self.minimum))

            if candidate_padded < minimum_padded:
                return False

        if self.maximum_exclusive is not None:
            width = max(len(candidate), len(self.maximum_exclusive))
            candidate_padded = candidate + (0,) * (width - len(candidate))
            maximum_padded = self.maximum_exclusive + (
                0,
            ) * (width - len(self.maximum_exclusive))

            if candidate_padded >= maximum_padded:
                return False

        return True


def demonstrate_constraint_intersection() -> None:
    """Show how two dependency constraints can be checked against versions."""

    print("\n=== Constraint Compatibility ===")

    service_a = VersionConstraint(
        package="httpx",
        minimum=(0, 27),
        maximum_exclusive=(1, 0),
    )

    service_b = VersionConstraint(
        package="httpx",
        minimum=(0, 28),
        maximum_exclusive=(1, 0),
    )

    candidates = ["0.26.0", "0.27.2", "0.28.1", "1.0.0"]

    for candidate in candidates:
        compatible = service_a.accepts(candidate) and service_b.accepts(candidate)
        print(f"httpx {candidate:7} compatible with both constraints: {compatible}")


# ---------------------------------------------------------------------------
# Import error diagnosis
# ---------------------------------------------------------------------------

def diagnose_import_error(module_name: str) -> None:
    """
    Diagnose common causes of an unavailable import without modifying
    the environment.
    """

    print(f"\n=== Import Diagnosis: {module_name} ===")

    spec = importlib.util.find_spec(module_name)

    if spec is not None:
        print("A module specification was found.")
        print("Origin:", spec.origin)
        return

    print("No module specification was found.")
    print("Python searches these locations in order:")
    for path in sys.path:
        print(" ", path)

    print(
        "A missing import may mean the dependency is not installed, "
        "the wrong interpreter is active, the package name differs from "
        "the import name, or the current project shadows the intended module."
    )


# ---------------------------------------------------------------------------
# Testing dependency behavior
# ---------------------------------------------------------------------------

def test_version_comparison() -> None:
    assert version_at_least("3.13.0", "3.11")
    assert version_at_least("2.0", "2.0")
    assert not version_at_least("2.9", "3.0")


def test_requirement_validation() -> None:
    assert validate_requirement_line("requests")
    assert validate_requirement_line("requests==2.32.5")
    assert validate_requirement_line("requests>=2.31,<3")
    assert not validate_requirement_line("requests=>2.0")


def test_constraint_intersection() -> None:
    constraint = VersionConstraint(
        package="demo",
        minimum=(2, 1),
        maximum_exclusive=(3, 0),
    )

    assert constraint.accepts("2.1.0")
    assert constraint.accepts("2.9.9")
    assert not constraint.accepts("2.0.9")
    assert not constraint.accepts("3.0.0")


def run_self_tests() -> None:
    """Run focused tests using only Python assertions."""

    print("\n=== Self Tests ===")

    tests = [
        test_version_comparison,
        test_requirement_validation,
        test_constraint_intersection,
    ]

    failures: list[str] = []

    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError:
            failures.append(test.__name__)
            print(f"FAIL: {test.__name__}")

    if failures:
        raise RuntimeError(f"Tests failed: {', '.join(failures)}")

    print("All tests passed.")


# ---------------------------------------------------------------------------
# Application-level dependency manifest
# ---------------------------------------------------------------------------

@dataclass
class ApplicationManifest:
    name: str
    python_requires: str
    dependencies: list[str]

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not self.name.strip():
            errors.append("Application name cannot be empty.")

        if not self.python_requires.startswith(">="):
            errors.append("Python requirement must begin with >=.")

        for dependency in self.dependencies:
            if not validate_requirement_line(dependency):
                errors.append(f"Invalid dependency declaration: {dependency}")

        return errors


def demonstrate_manifest() -> None:
    """Build and validate application dependency metadata."""

    print("\n=== Application Manifest ===")

    manifest = ApplicationManifest(
        name="repository-governance-tool",
        python_requires=">=3.11",
        dependencies=[
            "httpx>=0.27,<1",
            "pydantic>=2.0,<3",
        ],
    )

    errors = manifest.validate()

    if errors:
        print("Manifest validation failed:")
        for error in errors:
            print(" ", error)
    else:
        print(json.dumps(asdict(manifest), indent=2))


# ---------------------------------------------------------------------------
# Production-oriented observations
# ---------------------------------------------------------------------------

def demonstrate_runtime_information() -> None:
    """Display information useful when debugging dependency environments."""

    print("\n=== Runtime Diagnostics ===")
    print("Python version:", sys.version.split()[0])
    print("Executable:", sys.executable)
    print("Platform:", platform.platform())
    print("Implementation:", platform.python_implementation())
    print("Working directory:", Path.cwd())
    print("Virtual environment:", virtual_environment_state()["active"])

    # Dependency problems are often caused by invoking pip from one Python
    # installation and running the application with another. Using
    # `python -m pip` ties pip execution to the selected interpreter.
    print(
        "Recommended package-manager invocation pattern:",
        f'"{sys.executable}" -m pip ...',
    )


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main() -> None:
    demonstrate_basic_imports()
    demonstrate_import_styles()

    inspect_module("json")
    inspect_module("pathlib")

    demonstrate_importlib()
    demonstrate_local_package()
    demonstrate_standard_library()

    demonstrate_dependency_model()
    demonstrate_virtual_environment()
    demonstrate_package_manager()
    demonstrate_dependency_file()

    demonstrate_constraint_intersection()
    diagnose_import_error("module_that_is_not_installed")

    demonstrate_manifest()
    demonstrate_runtime_information()

    run_self_tests()

    print("\n=== Complete ===")
    print(
        "The demonstrations covered modules, imports, packages, standard-library "
        "usage, environment isolation, dependency declarations, compatibility "
        "constraints, diagnostics, and executable validation."
    )


if __name__ == "__main__":
    main()
