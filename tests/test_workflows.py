"""Keep the default branch and required security gate covered by CI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _workflow(name: str) -> dict:
    # BaseLoader preserves YAML's literal `on` key rather than interpreting it
    # as a YAML 1.1 boolean. GitHub uses it as an event name.
    return yaml.load((ROOT / ".github" / "workflows" / name).read_text(), Loader=yaml.BaseLoader)


def test_default_branch_is_covered_by_push_and_pr_checks():
    for name in ("ci.yml", "security.yml"):
        events = _workflow(name)["on"]
        for event in ("push", "pull_request"):
            configuration = events[event]
            branches = configuration.get("branches") if isinstance(configuration, dict) else None
            assert branches is None or "main" in branches


def test_protection_configuration_requires_existing_check_names():
    protection = json.loads((ROOT / ".github" / "branch-protection-main.json").read_text())
    names = set()
    for filename in ("ci.yml", "security.yml", "nexus-lane-guard.yml"):
        for job in _workflow(filename)["jobs"].values():
            name = job["name"]
            versions = job.get("strategy", {}).get("matrix", {}).get("python-version", [])
            if versions:
                names.update(name.replace("${{ matrix.python-version }}", version) for version in versions)
            else:
                names.add(name)
    required = set(protection["required_status_checks"]["contexts"])
    assert required <= names
    assert {
        "Lint (ruff)", "Type check (mypy)", "Package (installed wheel)",
        "Lane guard", "Security Scan Summary",
    } <= required
    assert all(f"Test (Python {version})" in required for version in ("3.12", "3.13", "3.14"))
    assert protection["required_status_checks"]["strict"] is True
    assert protection["enforce_admins"] is True
    assert protection["required_pull_request_reviews"]["required_approving_review_count"] >= 1
    assert protection["allow_force_pushes"] is False


@pytest.mark.skipif(shutil.which("bash") is None, reason="GitHub's gate runs in Bash")
@pytest.mark.parametrize("event,dependency,docker,changed,result,success", [
    ("pull_request", "success", "success", None, None, True),
    ("pull_request", "success", "skipped", None, None, False),
    ("push", "skipped", "success", None, None, True),
    ("workflow_dispatch", "skipped", "success", None, None, True),
    ("schedule", "skipped", "skipped", None, None, True),
    ("unknown", "skipped", "skipped", None, None, False),
    ("pull_request", "skipped", "skipped", None, None, False),
    ("pull_request", "failure", "skipped", None, None, False),
    ("pull_request", "success", "failure", None, None, False),
    ("push", "skipped", "skipped", None, None, False),
    ("push", "failure", "success", None, None, False),
    ("schedule", "skipped", "cancelled", None, None, False),
    ("pull_request", "success", "skipped", "PYTHON_SECURITY", "failure", False),
    ("pull_request", "success", "skipped", "SECRET_SCANNING", "cancelled", False),
    ("pull_request", "success", "skipped", "CODEQL_ANALYSIS", "skipped", False),
    ("pull_request", "success", "skipped", "WHEEL_AUDIT", "skipped", False),
])
def test_security_summary_exit_status(tmp_path, event, dependency, docker, changed, result, success):
    job = _workflow("security.yml")["jobs"]["security-summary"]
    assert {"python-security", "secret-scanning", "codeql-analysis", "dependency-review", "docker-security", "wheel-audit"} <= set(job["needs"])
    assert job["if"] == "always()"
    environment = {
        **os.environ,
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        "PYTHON_SECURITY": "success",
        "SECRET_SCANNING": "success",
        "CODEQL_ANALYSIS": "success",
        "DEPENDENCY_REVIEW": dependency,
        "DOCKER_SECURITY": docker,
        "WHEEL_AUDIT": "success",
        "EVENT_NAME": event,
    }
    if changed is not None:
        environment[changed] = result
    completed = subprocess.run(
        [shutil.which("bash"), "-c", job["steps"][0]["run"]],
        env=environment, capture_output=True, timeout=5, check=False,
    )
    assert (completed.returncode == 0) is success


def test_container_scan_fails_on_actionable_vulnerabilities():
    job = _workflow("security.yml")["jobs"]["docker-security"]
    gate = next(step for step in job["steps"] if step.get("name") == "Run Trivy in table format")
    assert gate["with"]["exit-code"] == "1"
    assert "'pull_request'" in job["if"]
    checkout = next(step for step in job["steps"] if step.get("name") == "Checkout code")
    assert checkout["with"]["persist-credentials"] == "false"


def test_runtime_image_excludes_build_only_uv_and_smoke_checks_imports():
    image = (ROOT / "Dockerfile.ui").read_text()
    assert "pip uninstall --yes uv" in image
    job = _workflow("security.yml")["jobs"]["docker-security"]
    smoke = next(step for step in job["steps"] if step.get("name") == "Verify runtime imports and exclude build tools")
    assert "docker run --rm" in smoke["run"]
    assert 'import streamlit' in smoke["run"]
    assert 'find_spec("uv") is None' in smoke["run"]
