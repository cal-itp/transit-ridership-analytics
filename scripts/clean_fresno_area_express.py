"""
Fresno Area Express
"""

import gcsfs
import pandas as pd
import time_utils
from shared_vars import AGENCY_TO_GTFS_NAME_DICT, LOCAL_FOLDER, RAW_DATA_YAML, RAW_GCS


def ingest_fresno_area_express(agency_name: str = "fresno_area_express") -> pd.DataFrame:
    """
    Import Fresno's Excel.
    Add day type, start and end date column to fit in staging table schema.
    """
    filename = RAW_DATA_YAML[agency_name][0]
    raw_fresno = pd.read_excel(f"{LOCAL_FOLDER}{agency_name}/{filename}", engine="openpyxl")

    raw_fresno_export = (
        raw_fresno.groupby(by=["Date", "StopID", "StopLabel"], dropna=False)[
            ["ProjectedBoarding", "ProjectedAlighting"]
        ]
        .sum()
        .reset_index()
    )

    raw_fresno_export["start_date"] = pd.to_datetime(raw_fresno_export["Date"])
    raw_fresno_export["end_date"] = pd.to_datetime(raw_fresno_export["Date"])
    raw_fresno_export["day_type"] = raw_fresno_export["Date"].apply(time_utils.get_day_type)
    raw_fresno_export["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]

    return raw_fresno_export


def rename_operator_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns to a shared schema.
    Use agency_config/*.yml to see what those names are.

    Create columns that add information about variation across operators
    - reporting_unit
    - ridership_measure
    - geographic grain
    - daily_ridership_basis
    """
    RENAME_COLS_DICT = {
        "Date": "date",
        "StopID": "stop_id",
        "StopLabel": "stop_name",
        "ProjectedBoarding": "avg_boardings",
        "ProjectedAlighting": "avg_alightings",
    }

    df = df.assign(
        reporting_unit="day", ridership_measure="daily", geography_grain="stop", daily_ridership_basis="reported_daily"
    ).rename(columns=RENAME_COLS_DICT)

    return df


if __name__ == "__main__":

    agency_name = "fresno_area_express"

    raw_fresno_export = ingest_fresno_area_express(agency_name)
    raw_fresno_export.to_parquet(f"{RAW_GCS}{agency_name}/ridership_round1.parquet", filesystem=gcsfs.GCSFileSystem())

    print(f"exported: {agency_name}")
