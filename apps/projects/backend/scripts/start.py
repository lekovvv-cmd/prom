"""Select Projects web or worker process in the shared image."""

import os
import subprocess


def enabled(name: str) -> bool:
    return os.getenv(name, "false").lower() == "true"


def main() -> None:
    process = os.getenv("PROJECTS_PROCESS", "web")
    if process == "worker":
        os.execvp("python", ["python", "-m", "scripts.worker"])
        return
    if process != "web":
        raise ValueError("PROJECTS_PROCESS must be web or worker")
    if enabled("PROM_RUN_MIGRATIONS"):
        subprocess.run(["python", "-m", "alembic", "upgrade", "head"], check=True)
    if enabled("PROM_SEED_PILOT"):
        subprocess.run(["python", "scripts/seed_pilot.py"], check=True)
    port = os.getenv("PORT", "8000")
    os.execvp(
        "python", ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port]
    )


if __name__ == "__main__":
    main()
