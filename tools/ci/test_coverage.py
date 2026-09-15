from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


CONFIG = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_coverage_counts_unexecuted_files_and_branches_and_enforces_threshold(tmp_path: Path):
    source = tmp_path / "sample"
    source.mkdir()
    (source / "decision.py").write_text(
        "def decide(flag):\n    if flag:\n        return 1\n    return 0\n",
        encoding="utf-8",
    )
    (source / "unexecuted.py").write_text("value = 42\n", encoding="utf-8")
    (source / "tests").mkdir()
    (source / "tests" / "fixture.py").write_text("fixture = 1\n", encoding="utf-8")
    (source / "alembic").mkdir()
    (source / "alembic" / "migration.py").write_text("migration = 1\n", encoding="utf-8")
    runner = tmp_path / "exercise.py"
    runner.write_text("from sample.decision import decide\nassert decide(True) == 1\n", encoding="utf-8")
    environment = {
        **os.environ,
        "COVERAGE_SOURCE": str(source),
        "COVERAGE_FILE": str(tmp_path / ".coverage"),
    }
    coverage = [sys.executable, "-m", "coverage"]
    subprocess.run(
        [*coverage, "run", f"--rcfile={CONFIG}", str(runner)],
        cwd=tmp_path, env=environment, check=True,
    )
    subprocess.run(
        [*coverage, "json", f"--rcfile={CONFIG}", "--fail-under=0", "-o", "coverage.json"],
        cwd=tmp_path, env=environment, check=True,
    )
    report = json.loads((tmp_path / "coverage.json").read_text(encoding="utf-8"))
    files = {Path(name).name: data for name, data in report["files"].items()}
    assert set(files) == {"decision.py", "unexecuted.py"}
    assert files["unexecuted.py"]["summary"]["covered_lines"] == 0
    assert files["decision.py"]["summary"]["num_branches"] == 2
    assert files["decision.py"]["summary"]["covered_branches"] == 1
    result = subprocess.run(
        [*coverage, "report", f"--rcfile={CONFIG}", "--fail-under=100"],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
    )
    assert result.returncode == 2, result.stdout + result.stderr
