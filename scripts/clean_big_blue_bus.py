"""
Big Blue Bus
Note: Each stop id can have more than 1 record.
"""

import gcsfs
import pandas as pd
from shared_vars import AGENCY_TO_GTFS_NAME_DICT, LOCAL_FOLDER, RAW_DATA_YAML, RAW_GCS


def ingest_big_blue_bus(agency_name: str = "big_blue_bus") -> pd.DataFrame:
    """
    Import Excel
    and add start and end date of service period/aggregation period.
    """
    filename = RAW_DATA_YAML[agency_name][0]
    raw_big_blue_bus = pd.read_excel(f"{LOCAL_FOLDER}{agency_name}/{filename}", engine="openpyxl")
    raw_big_blue_bus_export = (
        raw_big_blue_bus.groupby(
            [
                "SERVICE_PERIOD",
                "SERVICE_DAY",
                "ROUTE_NUMBER",
                "ROUTE_NAME",
                "DIRECTION_NAME",
                "STOP_ID",
                "STOP_NAME",
                "STOP_LAT",
                "STOP_LON",
            ],
            dropna=False,
        )[["AVERAGE_DAILY_BOARDINGS", "AVERAGE_DAILY_ALIGHTINGS"]]
        .sum()
        .reset_index()
    )

    raw_big_blue_bus_export["start_date"] = raw_big_blue_bus_export["SERVICE_PERIOD"]
    raw_big_blue_bus_export["end_date"] = raw_big_blue_bus_export["SERVICE_PERIOD"] + pd.offsets.MonthEnd(4)
    raw_big_blue_bus_export["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]

    return raw_big_blue_bus_export


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
        "SERVICE_DAY": "day_type",
        "ROUTE_NUMBER": "route_id",
        "ROUTE_NAME": "route_name",
        "DIRECTION_NAME": "direction",
        "STOP_ID": "stop_id",
        "STOP_NAME": "stop_name",
        "STOP_LAT": "stop_lat",
        "STOP_LON": "stop_lon",
        "AVERAGE_DAILY_BOARDINGS": "avg_boardings",
        "AVERAGE_DAILY_ALIGHTINGS": "avg_alightings",
    }

    df = df.assign(
        reporting_unit="custom_period",
        ridership_measure="avg_daily",
        geography_grain="stop",
        daily_ridership_basis="reported_avg_daily",
    ).rename(columns=RENAME_COLS_DICT)

    return df


if __name__ == "__main__":

    agency_name = "big_blue_bus"
    raw_big_blue_bus_export = ingest_big_blue_bus(agency_name)
    raw_big_blue_bus_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")
