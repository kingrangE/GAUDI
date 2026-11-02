"""Daily PostgreSQL dump + restore check + S3 upload, using Docker and AWS CLI."""

import argparse
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

DIRECTORY = Path(__file__).resolve().parent


def run(*args, **kwargs):
    # Bound stalled Docker/AWS commands; systemd also bounds the entire job.
    return subprocess.run(args, check=True, timeout=600, **kwargs)


def postgres(*args, **kwargs):
    return run(
        "docker", "compose", "--project-directory", str(DIRECTORY),
        "exec", "-T", "--user", "postgres", "postgres", *args, **kwargs,
    )


def restore_check(archive: Path) -> int:
    """Restore only into a new disposable database; never overwrite the live DB."""
    database = f"restore_check_{uuid4().hex}"
    postgres("createdb", "-U", "postgres", "--template=template0", database)
    try:
        with archive.open("rb") as source:
            postgres(
                "pg_restore", "-U", "postgres", "--dbname", database,
                "--single-transaction", "--exit-on-error", "--no-owner", "--no-acl",
                stdin=source,
            )
        result = postgres(
            "psql", "-U", "postgres", "-d", database, "-At", "-v", "ON_ERROR_STOP=1",
            "-c", "SELECT count(*) FROM pg_tables WHERE schemaname = 'public'",
            capture_output=True, text=True,
        )
        tables = int(result.stdout.strip())
        if tables == 0:
            raise ValueError("Restore contains no application tables")
        return tables
    finally:
        postgres("dropdb", "-U", "postgres", "--force", database)


def s3_prefix() -> str:
    prefix = os.environ.get("BACKUP_S3_PREFIX", "").rstrip("/")
    parts = prefix.removeprefix("s3://").split("/", 1)
    if not prefix.startswith("s3://") or len(parts) != 2 or not all(parts):
        raise ValueError("Set BACKUP_S3_PREFIX to s3://bucket/gaudi/postgres")
    return prefix + "/"


def backup() -> str:
    prefix = s3_prefix()
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = f"{prefix}{timestamp}-{uuid4().hex}.dump"
    # TemporaryDirectory is private to the job's OS user and cleaned on failure.
    with tempfile.TemporaryDirectory(prefix="gaudi-backup-") as directory:
        archive = Path(directory) / "gaudi.dump"
        with archive.open("wb") as target:
            postgres(
                "pg_dump", "-U", "postgres", "-d", "gaudi", "--format=custom",
                "--no-owner", "--no-acl", stdout=target,
            )
        tables = restore_check(archive)
        run(
            "aws", "s3", "cp", str(archive), destination, "--sse", "AES256",
            "--only-show-errors",
        )
    print(f"BACKUP_OK tables={tables} uri={destination}", flush=True)
    return destination


def verify(uri: str) -> int:
    if not uri.startswith(s3_prefix()) or not uri.endswith(".dump"):
        raise ValueError("Backup URI must be a .dump inside BACKUP_S3_PREFIX")
    with tempfile.TemporaryDirectory(prefix="gaudi-verify-") as directory:
        archive = Path(directory) / "gaudi.dump"
        run("aws", "s3", "cp", uri, str(archive), "--only-show-errors")
        tables = restore_check(archive)
    print(f"VERIFY_OK tables={tables} uri={uri}", flush=True)
    return tables


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("backup")
    commands.add_parser("verify").add_argument("uri")
    arguments = parser.parse_args()
    if arguments.command == "backup":
        backup()
    else:
        verify(arguments.uri)
