"""Exercise copied Lane guard remediation with hostile, valid git refs."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "branch",
    [
        "contrib/ordinary",
        "contrib/topic;touch${IFS}PWN",
        "contrib/$(touch${IFS}PWN)",
    ],
)
def test_copied_lane_guard_commands_preserve_branch_as_one_argument(tmp_path, branch):
    bash = shutil.which("bash")
    git = shutil.which("git")
    if not bash or not git:
        pytest.skip("Lane guard runs on a Linux runner with bash and git")
    subprocess.run([git, "check-ref-format", "--branch", branch], check=True, capture_output=True)

    workflow = yaml.load(
        (ROOT / ".github/workflows/nexus-lane-guard.yml").read_text(), Loader=yaml.BaseLoader,
    )
    script = workflow["jobs"]["lane"]["steps"][1]["run"]
    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake_git = bindir / "git"
    fake_git.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['GIT_CALLS'], 'a') as output:\n"
        "    output.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "if sys.argv[1] == 'diff':\n"
        "    print('LICENSE')\n"
    )
    fake_git.chmod(0o755)
    summary = tmp_path / "summary.md"
    calls = tmp_path / "git-calls.jsonl"
    env = {
        **os.environ,
        "PATH": str(bindir) + os.pathsep + os.environ["PATH"],
        "HEAD_REF": branch,
        "HEAD_SHA": "a" * 40,
        "UPSTREAM_URL": "https://example.invalid/upstream.git",
        "UPSTREAM_BRANCH": "master",
        "GITHUB_STEP_SUMMARY": str(summary),
        "GIT_CALLS": str(calls),
    }
    guarded = subprocess.run(
        [bash, "-c", script], cwd=tmp_path, env=env, capture_output=True, text=True,
    )
    assert guarded.returncode == 1
    commands = summary.read_text().split("```bash\n", 1)[1].split("```", 1)[0]
    subprocess.run([bash, "-c", commands], cwd=tmp_path, env=env, check=True)

    recorded = [json.loads(line) for line in calls.read_text().splitlines()]
    assert ["rebase", "--onto", "upstream/master", "origin/main", branch] in recorded
    assert ["push", "--force-with-lease", "origin", branch] in recorded
    assert not (tmp_path / "PWN").exists()
