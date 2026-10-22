"""Regression coverage for the PaaS service dispatcher, independent of Docker."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "relaxdev_runtime", Path(__file__).resolve().parents[2] / "deploy/relaxdev/runtime.py"
)
assert spec is not None and spec.loader is not None
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


@pytest.fixture
def launch(monkeypatch):
    calls = []
    monkeypatch.setattr(runtime.sys, "argv", ["runtime.py"])
    monkeypatch.setattr(runtime.os, "chdir", lambda path: calls.append(("cwd", path)))
    monkeypatch.setattr(runtime.os, "execv", lambda *args: calls.append(("exec", *args)))
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("PROM_SERVICE", raising=False)
    return calls


def test_default_role_runs_shell(launch):
    runtime.main()
    assert launch == [("exec", "/start-relaxdev.sh", ["/start-relaxdev.sh"])]


@pytest.mark.parametrize("role,service", [("access", "access"), ("projects", "projects")])
def test_backend_uses_its_isolated_environment(role, service, launch, monkeypatch):
    monkeypatch.setenv("PROM_SERVICE", role)
    runtime.main()
    python = str(Path(f"/opt/{service}-venv/bin/python"))
    assert launch == [
        ("cwd", f"/workspace/{service}"),
        ("exec", python, [python, "scripts/start.py"]),
    ]
    assert runtime.os.environ["PATH"].startswith(str(Path(f"/opt/{service}-venv/bin")) + ":")
    assert runtime.os.environ["PORT"] == "8080"


def test_worker_exposes_platform_port_and_selects_worker(launch, monkeypatch):
    monkeypatch.setenv("PROM_SERVICE", "worker")
    monkeypatch.setenv("PORT", "18080")
    monkeypatch.setenv("PROJECTS_WORKER_METRICS_PORT", "9100")
    runtime.main()
    assert runtime.os.environ["PROJECTS_PROCESS"] == "worker"
    assert runtime.os.environ["PROJECTS_WORKER_METRICS_PORT"] == "18080"
    assert launch[-1][-1][-1] == "scripts/start.py"


def test_worker_health_checks_job_heartbeats(launch, monkeypatch):
    monkeypatch.setenv("PROM_SERVICE", "worker")
    monkeypatch.setattr(runtime.sys, "argv", ["runtime.py", "--health"])
    runtime.main()
    assert launch[-1][-1][1:] == ["-m", "scripts.worker", "--health"]


def test_invalid_role_fails_without_starting_a_service(launch, monkeypatch):
    monkeypatch.setenv("PROM_SERVICE", "invalid")
    with pytest.raises(ValueError, match="PROM_SERVICE"):
        runtime.main()
    assert not launch
