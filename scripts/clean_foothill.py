"""
Foothill Transit
Infer column names.
Aggregate trip-stop data to stop-level.
"""

import calendar

import gcsfs
import pandas as pd
import time_utils
from shared_vars import AGENCY_TO_GTFS_NAME_DICT, LOCAL_FOLDER, RAW_DATA_YAML, RAW_GCS


def ingest_foothill_transit(
    agency_name: str = "foothill_transit",
) -> pd.DataFrame:
    """
    Import Foothill Transit Excel.
    Add column names to the raw data since it doesn't come with headers.
    Aggregate the inferred boardings/aligtings columns to stop, route, direction level from trip-stop level.
    Each stop may appear multiple times if it serves multiple routes.
    """
    filename = RAW_DATA_YAML[agency_name][0]


    # import data with inferred column names
    column_names=["unknown_1", "date", "unknown_2", "block_id", "route_short_name", "unknown_3", "direction", "stop_code", "unknown_4",
              "unknown_5", "unknown_6", "stop_lat", "stop_lon", "boardings", "alightings", "max_load"]
    
    raw_foothill_transit = pd.read_csv(
        f"{LOCAL_FOLDER}{agency_name}/{filename}",
        encoding="utf-8",
        header=None, 
        names=column_names
    )

    # aggregate to route-direction-stop level (not sure the level of detail in raw since it doesn't come with header)
    raw_foothill_transit["date"] = pd.to_datetime(raw_foothill_transit["date"]).dt.floor('D')
    
    raw_foothill_transit_export = (
        raw_foothill_transit.groupby(by=["date", "route_short_name", "direction", "stop_code", "stop_lat", "stop_lon"], as_index=False, dropna=False)
            .agg(boardings = ("boardings", "sum"), 
                 alightings = ("alightings", "sum"))
    )

    raw_foothill_transit_export["start_date"] = raw_foothill_transit_export["date"]
    raw_foothill_transit_export["end_date"] = raw_foothill_transit_export["date"]
    raw_foothill_transit_export["day_type"] = raw_foothill_transit_export["date"].apply(time_utils.get_day_type)
    raw_foothill_transit_export["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]

    return raw_foothill_transit_export

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
        "route_short_name": "route_id",
        "stop_code": "stop_id",
        "boardings": "avg_boardings",
        "alightings": "avg_alightings",
        "lat": "stop_lat",
        "lon": "stop_lon"
    }

    df = df.assign(
        reporting_unit="day",
        ridership_measure="daily",
        geography_grain="trip_stop",
        daily_ridership_basis="reported_daily",
    ).rename(columns=RENAME_COLS_DICT)

    return df


if __name__ == "__main__":

    agency_name = "foothill_transit"

    raw_foothill_transit_export = ingest_foothill_transit(agency_name)
    raw_foothill_transit_export.to_parquet(f"{RAW_GCS}{agency_name}/ridership_round1.parquet", filesystem=gcsfs.GCSFileSystem())

    print(f"exported: {agency_name}")