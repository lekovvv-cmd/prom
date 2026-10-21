"""PaaS startup; Compose may continue to override the container command."""

import os
import subprocess


def enabled(name: str) -> bool:
    return os.getenv(name, "false").lower() == "true"


def main() -> None:
    if enabled("PROM_RUN_MIGRATIONS"):
        subprocess.run(["python", "scripts/init_db.py"], check=True)
    if enabled("PROM_SEED_PILOT"):
        subprocess.run(["python", "scripts/seed_pilot.py"], check=True)
    port = os.getenv("PORT", "8002")
    os.execvp(
        "python",
        [
            "python",
            "-m",
            "uvicorn",
            "access_service.bootstrap.app:app",
            "--host",
            "0.0.0.0",
            "--port",
            port,
        ],
    )


if __name__ == "__main__":
    main()
