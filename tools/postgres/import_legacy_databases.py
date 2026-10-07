"""One-time, transactional import from the three previous local DB containers."""

from __future__ import annotations

import subprocess
import time

DATABASES = (
    ("prom-access-db-1", "prom_access"),
    ("prom-projects-db-1", "project_showcase"),
    ("prom-service-desk-db-1", "service_desk"),
)
NEW_CONTAINER = "prom-postgres-1"


def query(container: str, user: str, database: str, sql: str) -> str:
    result = subprocess.run(
        ["docker", "exec", container, "psql", "-At", "-U", user, "-d", database, "-c", sql],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    table_count = "SELECT count(*) FROM pg_tables WHERE schemaname = 'public'"
    for old_container, database in DATABASES:
        if query(NEW_CONTAINER, database, database, table_count) != "0":
            print(f"Shared database {database} already has tables; preserving it", flush=True)
            continue
        running = subprocess.run(
            ["docker", "container", "inspect", "--format", "{{.State.Running}}", old_container],
            capture_output=True,
            text=True,
            check=False,
        )
        if running.returncode != 0:
            continue
        if running.stdout.strip() != "true":
            subprocess.run(
                ["docker", "start", old_container],
                check=True,
                stdout=subprocess.DEVNULL,
            )
        for _ in range(30):
            ready = subprocess.run(
                ["docker", "exec", old_container, "pg_isready", "-U", database, "-d", database],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if ready.returncode == 0:
                break
            time.sleep(2)
        else:
            raise RuntimeError(f"Legacy database {old_container} did not become ready")
        if query(old_container, database, database, table_count) == "0":
            continue

        print(f"Importing existing {database} data into shared PostgreSQL", flush=True)
        dump = subprocess.Popen(
            [
                "docker",
                "exec",
                old_container,
                "pg_dump",
                "-Fc",
                "--no-owner",
                "--no-acl",
                "-U",
                database,
                "-d",
                database,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert dump.stdout is not None
        restore = subprocess.Popen(
            [
                "docker",
                "exec",
                "-i",
                NEW_CONTAINER,
                "pg_restore",
                "--single-transaction",
                "--exit-on-error",
                "--no-owner",
                "--no-acl",
                "-U",
                database,
                "-d",
                database,
            ],
            stdin=dump.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        dump.stdout.close()
        dump.stdout = None
        _, restore_error = restore.communicate()
        _, dump_error = dump.communicate()
        if dump.returncode != 0 or restore.returncode != 0:
            raise RuntimeError(
                f"Could not import {database}: dump={dump.returncode}, restore={restore.returncode}; "
                f"{dump_error.decode(errors='replace')} {restore_error.decode(errors='replace')}"
            )
        print(f"Imported {database}", flush=True)


if __name__ == "__main__":
    main()
