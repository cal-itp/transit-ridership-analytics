"""
OCTA
"""

import gcsfs
import pandas as pd
import time_utils
from shared_vars import AGENCY_TO_GTFS_NAME_DICT, LOCAL_FOLDER, RAW_DATA_YAML, RAW_GCS


def ingest_octa(
    agency_name: str = "octa",
) -> pd.DataFrame:
    """
    Import OCTA Excvel.
    Aggregate trip-stop/event level (door open/close) ridership to
    stop level ridership.
    Looks like raw stop name has stop id as prefix.
    Extract stop id from stop name.
    """
    filename = RAW_DATA_YAML[agency_name][0]

    raw_octa = pd.read_excel(
        f"{LOCAL_FOLDER}{agency_name}/{filename}",
        skiprows=[1],
        engine="openpyxl",
    )

    raw_octa_export = (
        raw_octa.groupby(
            by=["Cal Year", "Month", "Trans Date", "Day of Week", "Route", "Direction", "Stop Name"], dropna=False
        )[["APC Boarding", "APC Alighting"]]
        .sum()
        .reset_index()
    )

    raw_octa_export["stop_id"] = raw_octa_export["Stop Name"].str.extract(r"^\s*(\d+)\s*[--]\s*")
    raw_octa_export["route_id"] = raw_octa_export["Route"].str.extract(r"^\s*(\d+)\s*[--]\s*")
    raw_octa_export["Trans Date"] = pd.to_datetime(raw_octa_export["Trans Date"], errors="coerce")
    raw_octa_export["day_type"] = raw_octa_export["Trans Date"].apply(time_utils.get_day_type)
    raw_octa_export["start_date"] = pd.to_datetime(raw_octa_export["Trans Date"])
    raw_octa_export["end_date"] = pd.to_datetime(raw_octa_export["Trans Date"])
    raw_octa_export["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]

    return raw_octa_export


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
        "Route": "route_name",
        "Direction": "direction",
        "stop_id": "stop_id",
        "Stop Name": "stop_name",
        "APC Boarding": "avg_boardings",
        "APC Alighting": "avg_alightings",
    }

    df = df.assign(
        reporting_unit="day",
        ridership_measure="daily",
        geography_grain="trip_stop",
        daily_ridership_basis="reported_daily",
    ).rename(columns=RENAME_COLS_DICT)

    return df


if __name__ == "__main__":

    agency_name = "octa"

    raw_octa_export = ingest_octa(agency_name)
    raw_octa_export.to_parquet(f"{RAW_GCS}{agency_name}/ridership_round1.parquet", filesystem=gcsfs.GCSFileSystem())

    print(f"exported: {agency_name}")
