from __future__ import annotations

import argparse
from pathlib import Path

from access_service.bootstrap.config import settings
from access_service.infrastructure.database import SessionLocal
from access_service.infrastructure.identity import DatabaseSigningKeyStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Rotate the Access Service JWT signing key")
    parser.add_argument("--kid", help="Unique id for the new active key")
    parser.add_argument("--private-key-file", type=Path)
    parser.add_argument("--retire-expired", action="store_true")
    args = parser.parse_args()
    store = DatabaseSigningKeyStore(settings, SessionLocal)
    if args.retire_expired:
        count = store.retire_expired()
        print(f"Retired {count} expired verification key(s)")
        return
    if not args.kid:
        parser.error("--kid is required unless --retire-expired is used")
    private_key = (
        args.private_key_file.read_text(encoding="utf-8")
        if args.private_key_file is not None
        else None
    )
    store.rotate(kid=args.kid, private_key_pem=private_key)
    print(f"Activated signing key {args.kid}; previous key remains verify-only during overlap")


if __name__ == "__main__":
    main()
