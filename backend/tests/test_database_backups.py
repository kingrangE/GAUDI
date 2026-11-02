"""Backup failure handling plus an opt-in real PostgreSQL recovery drill."""

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "deploy/postgres"
spec = importlib.util.spec_from_file_location("db_backup", SOURCE / "backup.py")
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


@pytest.fixture
def fake_commands(monkeypatch):
    calls = []
    monkeypatch.setenv("BACKUP_S3_PREFIX", "s3://test-bucket/gaudi/postgres")

    def postgres(*args, **kwargs):
        calls.append(args)
        if args[0] == "pg_dump":
            kwargs["stdout"].write(b"archive")
        return SimpleNamespace(stdout="1\n")

    monkeypatch.setattr(backup, "postgres", postgres)
    monkeypatch.setattr(backup, "run", lambda *args, **kwargs: calls.append(args))
    return calls


def test_backup_restores_before_upload_and_cleans_file(fake_commands):
    uri = backup.backup()
    assert uri.startswith("s3://test-bucket/gaudi/postgres/")
    assert uri.endswith(".dump")
    assert [call[0] for call in fake_commands] == [
        "pg_dump", "createdb", "pg_restore", "psql", "dropdb", "aws",
    ]
    assert not Path(fake_commands[-1][3]).exists()


@pytest.mark.parametrize("failed_command", ["pg_dump", "pg_restore", "aws"])
def test_failed_backup_never_reports_success(fake_commands, monkeypatch, capsys, failed_command):
    original_postgres = backup.postgres

    def postgres(*args, **kwargs):
        if args[0] == failed_command:
            raise subprocess.CalledProcessError(1, args[0])
        return original_postgres(*args, **kwargs)

    def aws(*args, **kwargs):
        if failed_command == "aws":
            raise subprocess.CalledProcessError(1, "aws")
        pytest.fail("Must not upload an invalid backup")

    monkeypatch.setattr(backup, "postgres", postgres)
    monkeypatch.setattr(backup, "run", aws)
    with pytest.raises(subprocess.CalledProcessError):
        backup.backup()
    assert "BACKUP_OK" not in capsys.readouterr().out
    if failed_command == "pg_restore":
        assert fake_commands[-1][0] == "dropdb"


def test_empty_database_is_not_a_successful_backup(fake_commands, monkeypatch):
    original = backup.postgres

    def postgres(*args, **kwargs):
        result = original(*args, **kwargs)
        return SimpleNamespace(stdout="0\n") if args[0] == "psql" else result

    monkeypatch.setattr(backup, "postgres", postgres)
    with pytest.raises(ValueError, match="no application tables"):
        backup.backup()
    assert fake_commands[-1][0] == "dropdb"


@pytest.mark.parametrize("prefix", ["", "https://bucket/prefix", "s3://bucket", "s3:///prefix"])
def test_invalid_destination_fails_before_dump(monkeypatch, prefix):
    monkeypatch.setenv("BACKUP_S3_PREFIX", prefix)
    with pytest.raises(ValueError, match="BACKUP_S3_PREFIX"):
        backup.backup()


@pytest.mark.parametrize("uri", [
    "s3://other-bucket/gaudi/postgres/a.dump",
    "s3://test-bucket/gaudi/postgres-other/a.dump",
    "s3://test-bucket/gaudi/postgres/a.sql",
])
def test_verify_rejects_unexpected_sources(fake_commands, uri):
    with pytest.raises(ValueError, match="Backup URI"):
        backup.verify(uri)
    assert not fake_commands


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_BACKUP_TESTS") != "1", reason="Needs local Docker")
def test_real_dump_upload_download_restore_and_corruption(tmp_path, monkeypatch):
    # Only S3 is replaced with a local object; PostgreSQL and dump/restore are real.
    for name in ("compose.yaml", "init-app.sql"):
        shutil.copy(SOURCE / name, tmp_path / name)
    (tmp_path / ".env").write_text(
        "POSTGRES_PASSWORD=local_test_admin\nAPP_DB_PASSWORD=local_test_app\n"
        "DB_BIND_IP=127.0.0.1\n"
    )
    # A random host port and project keep the drill away from development/production data.
    compose = tmp_path / "compose.yaml"
    compose.write_text(compose.read_text().replace(
        'name: gaudi-db', f'name: gaudi-backup-test-{backup.uuid4().hex}'
    ).replace(":5432:5432", ":0:5432"))
    monkeypatch.setattr(backup, "DIRECTORY", tmp_path)
    monkeypatch.setenv("BACKUP_S3_PREFIX", "s3://test-bucket/gaudi/postgres")
    original_run = backup.run
    original_postgres = backup.postgres
    stored = tmp_path / "s3-object.dump"
    restored_values = []

    def run(*args, **kwargs):
        if args[:3] == ("aws", "s3", "cp"):
            if args[3].startswith("s3://"):
                shutil.copy(stored, args[4])
            else:
                shutil.copy(args[3], stored)
            return None
        return original_run(*args, **kwargs)

    def postgres(*args, **kwargs):
        if args[0] == "dropdb":
            result = original_postgres(
                "psql", "-U", "postgres", "-d", args[-1], "-Atc",
                "SELECT value FROM recovery_probe", capture_output=True, text=True,
            )
            restored_values.append(result.stdout.strip())
        return original_postgres(*args, **kwargs)

    monkeypatch.setattr(backup, "run", run)
    compose_command = ("docker", "compose", "--project-directory", str(tmp_path))
    try:
        run(*compose_command, "up", "-d", "--wait")
        original_postgres(
            "psql", "-U", "postgres", "-d", "gaudi", "-v", "ON_ERROR_STOP=1", "-c",
            "SET ROLE gaudi_app; CREATE TABLE recovery_probe (value text); "
            "INSERT INTO recovery_probe VALUES ('preserved');",
        )
        role = original_postgres(
            "psql", "-U", "postgres", "-d", "gaudi", "-Atc",
            "SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication "
            "FROM pg_roles WHERE rolname = 'gaudi_app'", capture_output=True, text=True,
        )
        assert role.stdout.strip() == "f"
        monkeypatch.setattr(backup, "postgres", postgres)
        uri = backup.backup()
        original_postgres(
            "psql", "-U", "postgres", "-d", "gaudi", "-c",
            "UPDATE recovery_probe SET value = 'live-change'",
        )
        assert backup.verify(uri) == 1
        assert restored_values == ["preserved", "preserved"]
        live = original_postgres(
            "psql", "-U", "postgres", "-d", "gaudi", "-Atc",
            "SELECT value FROM recovery_probe", capture_output=True, text=True,
        )
        assert live.stdout.strip() == "live-change"
        # Rebuild on an empty database using the runbook's application ownership.
        recovery_database = "recovery_target"
        original_postgres("createdb", "-U", "postgres", "-O", "gaudi_app", recovery_database)
        with stored.open("rb") as archive:
            original_postgres(
                "pg_restore", "-U", "postgres", "-d", recovery_database,
                "--role=gaudi_app", "--no-owner", "--no-acl",
                "--single-transaction", "--exit-on-error", stdin=archive,
            )
        recovered = original_postgres(
            "psql", "-U", "postgres", "-d", recovery_database,
            "-v", "ON_ERROR_STOP=1", "-Atc",
            "SET ROLE gaudi_app; INSERT INTO recovery_probe VALUES ('new-write'); "
            "SELECT value FROM recovery_probe ORDER BY value", capture_output=True, text=True,
        )
        assert recovered.stdout.strip().splitlines()[-2:] == ["new-write", "preserved"]
        original_postgres("dropdb", "-U", "postgres", recovery_database)
        # Remove the row-check hook before testing a deliberately invalid archive.
        monkeypatch.setattr(backup, "postgres", original_postgres)
        stored.write_bytes(b"not a PostgreSQL archive")
        with pytest.raises(subprocess.CalledProcessError):
            backup.verify(uri)
        databases = original_postgres(
            "psql", "-U", "postgres", "-Atc",
            "SELECT datname FROM pg_database WHERE datname LIKE 'restore_check_%'",
            capture_output=True, text=True,
        )
        assert not databases.stdout.strip()
    except Exception:
        run(*compose_command, "logs", "--tail", "60")
        raise
    finally:
        run(*compose_command, "down", "--volumes")
