"""
Golden Gate Transit
"""
import gcsfs
import pandas as pd

import time_utils
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_golden_gate_transit(
    agency_name: str = "golden_gate_transit",
) -> pd.DataFrame:
    """
    Import Golden Gate csv.
    Aggregate to stop level. The raw data has trip-stop grain.
    """
    filename = RAW_DATA_YAML[agency_name][0]
    
    raw_ggt = pd.read_csv(
	    f"{LOCAL_FOLDER}{agency_name}/{filename}", encoding="utf-8"
	)
    # filter out virtual time points
    t_df_ggt = raw_ggt[raw_ggt["POINT_ROLE"].isin(["ST", "S"])]

    raw_ggt_export = raw_ggt.groupby(
        by=["OPERATION_DATE", "ROUTE", "DIRECTION", "STOP_NUMBER", "STOP_NAME"], dropna=False
    )[["BOARDINGS", "ALIGHTINGS"]].sum().reset_index()

   
    raw_ggt_export["date"] = pd.to_datetime(raw_ggt_export["OPERATION_DATE"], format="%d-%b-%y")
    raw_ggt_export["start_date"] = raw_ggt_export["date"]
    raw_ggt_export["end_date"] = raw_ggt_export["date"]
    raw_ggt_export["day_type"] = raw_ggt_export["date"].apply(time_utils.get_day_type)
    raw_ggt_export["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    
    return raw_ggt_export
    
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
        "ROUTE": "route_id",
        "DIRECTION": "direction",
        "STOP_NUMBER": "stop_id",
        "STOP_NAME": "stop_name",
        "BOARDINGS": "avg_boardings",
        "ALIGHTINGS": "avg_alightings"
    }
    
    df = df.assign(
        reporting_unit = "day",
        ridership_measure = "daily",
        geography_grain: "trip_stop",
        daily_ridership_basis = "reported_daily"
    ).rename(columns = RENAME_COLS_DICT)
    
    return df
    
if __name__ == "__main__":
   
    agency_name = "golden_gate_transit"
    
    raw_ggt_export = ingest_golden_gate_transit(agency_name)
    raw_ggt_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")