from __future__ import annotations

from pathlib import Path

import pandas as pd

import paos.ingest as ingest


def test_load_daily_log_routes_to_csv(monkeypatch, tmp_path: Path) -> None:
    # Arrange: patch paos.ingest.csv_ingest.ingest_csv to avoid real file IO
    def fake_ingest_csv(path: Path) -> pd.DataFrame:
        # Ensure we pass a Path and that it matches what we sent in
        assert isinstance(path, Path)
        assert path == tmp_path / "daily_log.csv"
        return pd.DataFrame({"source": ["csv"]})

    import paos.ingest.csv_ingest as csv_ingest
    monkeypatch.setattr(csv_ingest, "ingest_csv", fake_ingest_csv, raising=True)

    # Act
    df = ingest.load_daily_log("csv", path=tmp_path / "daily_log.csv")

    # Assert
    assert df.loc[0, "source"] == "csv"


def test_load_daily_log_routes_to_sheets(monkeypatch) -> None:
    # Arrange: patch read_daily_log_from_sheets to avoid real API calls
    def fake_read_daily_log_from_sheets(cfg, dump_raw_path=None) -> pd.DataFrame:
        # We only care that cfg has the fields we passed in
        assert cfg.spreadsheet_id == "SHEET_ID"
        assert cfg.range_ == "Form Responses 1!A1:J"
        return pd.DataFrame({"source": ["sheets"]})

    import paos.ingest.sheets_ingest as sheets_ingest
    monkeypatch.setattr(
        sheets_ingest,
        "read_daily_log_from_sheets",
        fake_read_daily_log_from_sheets,
        raising=True,
    )

    # Act
    df = ingest.load_daily_log(
        "sheets",
        spreadsheet_id="SHEET_ID",
        range_="Form Responses 1!A1:J",
    )

    # Assert
    assert df.loc[0, "source"] == "sheets"


def test_load_daily_log_forwards_dump_raw_path(monkeypatch) -> None:
    # Arrange: patch read_daily_log_from_sheets to capture dump_raw_path
    captured: dict[str, object] = {}

    def fake_read_daily_log_from_sheets(cfg, dump_raw_path=None) -> pd.DataFrame:
        captured["spreadsheet_id"] = cfg.spreadsheet_id
        captured["range_"] = cfg.range_
        captured["dump_raw_path"] = dump_raw_path
        return pd.DataFrame({"source": ["sheets"]})

    import paos.ingest.sheets_ingest as sheets_ingest
    monkeypatch.setattr(
        sheets_ingest,
        "read_daily_log_from_sheets",
        fake_read_daily_log_from_sheets,
        raising=True,
    )

    # Act
    df = ingest.load_daily_log(
        "sheets",
        spreadsheet_id="SHEET_ID",
        range_="Form Responses 1!A1:J",
        dump_raw_path="data/processed/sheets_raw.csv",
    )

    # Assert
    assert df.loc[0, "source"] == "sheets"
    assert captured["spreadsheet_id"] == "SHEET_ID"
    assert captured["range_"] == "Form Responses 1!A1:J"
    assert captured["dump_raw_path"] == "data/processed/sheets_raw.csv"
