from src.paos.ingest.sheets_ingest import SheetsConfig, read_daily_log_from_sheets

cfg = SheetsConfig(
    spreadsheet_id="1Ma4p5j8CW4EO98a2Xx6HBkUjTrt46o6-xL8ZpLxmk9U",
    range_="Form Responses 1!A1:J20",
)

df = read_daily_log_from_sheets(cfg)
print(df.head())
print(df.columns.tolist())
