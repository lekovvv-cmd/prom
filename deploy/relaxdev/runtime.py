"""Run one service from the image accepted by RelaxDev's root-Dockerfile builder."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from urllib.request import urlopen


def main() -> None:
    role = os.environ.get("PROM_SERVICE", "shell")
    if role not in {"access", "projects", "worker", "shell"}:
        raise ValueError("PROM_SERVICE must be access, projects, worker or shell")
    port = os.environ.setdefault("PORT", "8080")
    health = "--health" in sys.argv
    if role == "shell":
        if health:
            with urlopen(f"http://127.0.0.1:{port}/healthz", timeout=3) as response:
                if response.status != 200:
                    raise RuntimeError("Shell is not ready")
        else:
            os.execv("/start-relaxdev.sh", ["/start-relaxdev.sh"])
        return

    service = "access" if role == "access" else "projects"
    venv = Path(f"/opt/{service}-venv/bin")
    os.environ["PATH"] = f"{venv}:{os.environ.get('PATH', '')}"
    os.chdir(f"/workspace/{service}")
    if role == "worker":
        os.environ["PROJECTS_PROCESS"] = "worker"
        # RelaxDev checks port 8080 even for background services.
        os.environ["PROJECTS_WORKER_METRICS_PORT"] = port
        if health:
            os.execv(str(venv / "python"), [str(venv / "python"), "-m", "scripts.worker", "--health"])
            return
    elif role == "projects":
        os.environ["PROJECTS_PROCESS"] = "web"
    if health:
        with urlopen(f"http://127.0.0.1:{port}/health/ready", timeout=3) as response:
            if response.status != 200:
                raise RuntimeError(f"{service} is not ready")
    else:
        os.execv(str(venv / "python"), [str(venv / "python"), "scripts/start.py"])


if __name__ == "__main__":
    main()
