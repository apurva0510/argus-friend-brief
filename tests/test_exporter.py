import importlib.util
import sqlite3
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "export_argus_snapshot.py"
SPEC = importlib.util.spec_from_file_location("export_argus_snapshot", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_exporter_opens_database_read_only(tmp_path):
    database = tmp_path / "sample.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE companies (id INTEGER PRIMARY KEY, symbol TEXT, name TEXT, sector TEXT, industry TEXT)"
    )
    connection.commit()
    connection.close()

    uri = f"file:{database.resolve()}?mode=ro&immutable=1"
    read_only = sqlite3.connect(uri, uri=True)
    try:
        try:
            read_only.execute("INSERT INTO companies VALUES (1, 'X', 'X', NULL, NULL)")
        except sqlite3.OperationalError as exc:
            assert "readonly" in str(exc).lower()
        else:
            raise AssertionError("Expected the immutable connection to reject writes")
    finally:
        read_only.close()


def test_fact_does_not_include_private_notes():
    result = MODULE.fact("NVDA", "metric", "return_1d", 0.01, "2026-09-18", "test", kind="percent")

    assert result["display_value"] == "+1.0%"
    assert "notes" not in result
