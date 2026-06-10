"""
San Diego MTS
"""

import gcsfs
import pandas as pd
from shared_vars import AGENCY_TO_GTFS_NAME_DICT, LOCAL_FOLDER, RAW_DATA_YAML, RAW_GCS


def ingest_sdmts(agency_name: str = "sdmts") -> pd.DataFrame:
    """
    Import only the bus and trolley Excel.

    Agg to stop level. The raw data is avg ridership for each trip-stop.
    Note: Same stop ID can have more than on Stop Sequence in this dataset.
    In agg, stop sequence is not included.
    """
    list_of_files = list(RAW_DATA_YAML[agency_name][:2])

    raw_mts = pd.concat(
        [pd.read_csv(f"{LOCAL_FOLDER}{agency_name}/{filename}") for filename in list_of_files],
        axis=0,
        ignore_index=True,
    )

    raw_mts.columns = raw_mts.columns.str.strip()
    raw_mts_export = (
        raw_mts.groupby(
            [
                "Schedule Period",
                "Day Of Week",
                "Route",
                "Route Name",
                "Stop ID",
                "Stop Name",
                "Direction ID",
                "Direction Label",
            ],
            dropna=False,
        )[["Average On", "Average Off"]]
        .sum()
        .reset_index()
    )

    day_type_map = {"1-Weekday": "Weekday", "2-Saturday": "Saturday", "3-Sunday": "Sunday"}

    raw_mts_export[["start_date_str", "end_date_str"]] = raw_mts_export["Schedule Period"].str.extract(
        r"([A-Za-z]+\s*\d{1,2},\s*\d{4})\s*-\s*([A-Za-z]+\s*\d{1,2},\s*\d{4})"
    )

    raw_mts_export = raw_mts_export.assign(
        day_type=raw_mts_export["Day Of Week"].map(day_type_map),
        start_date=pd.to_datetime(raw_mts_export["start_date_str"]),
        end_date=pd.to_datetime(raw_mts_export["end_date_str"]),
        schedule_name=AGENCY_TO_GTFS_NAME_DICT[agency_name],
    ).drop(columns=["start_date_str", "end_date_str"])

    return raw_mts_export


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
        "Route": "route_id",
        "Route Name": "route_name",
        "Direction Label": "direction",
        "Stop ID": "stop_id",
        "Stop Name": "stop_name",
        "Average On": "avg_boardings",
        "Average Off": "avg_alightings",
    }

    df = df.assign(
        reporting_unit="custom_period",
        ridership_measure="avg_daily",
        geography_grain="trip_stop",
        daily_ridership_basis="reported_avg_daily",
    ).rename(columns=RENAME_COLS_DICT)

    return df


if __name__ == "__main__":

    agency_name = "sdmts"

    raw_mts_export = ingest_sdmts(agency_name)
    raw_mts_export.to_parquet(f"{RAW_GCS}{agency_name}/ridership_round1.parquet", filesystem=gcsfs.GCSFileSystem())

    print(f"exported: {agency_name}")
