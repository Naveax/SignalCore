from __future__ import annotations

from syntavra_runtime.headless_runtime import HeadlessRuntime


def test_headless_runtime_releases_sqlite_file_handle(tmp_path) -> None:
    database = tmp_path / "headless.sqlite3"
    runtime = HeadlessRuntime(database, tmp_path / "state")

    assert runtime.stats()["ok"] is True

    moved = tmp_path / "headless.moved.sqlite3"
    database.replace(moved)
    moved.replace(database)
    assert database.is_file()
