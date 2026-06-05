"""
SamTrans

Look at Riverside too and see if both of these can follow a 
similar workflow to upload parquets in two stages
"""
import gcsfs
import pandas as pd

from pathlib import Path

import time_utils
from shared_vars import LOCAL_FOLDER, AGENCY_GCS, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def export_excel_as_parquet(
    agency_name: str,
    list_of_files: list,
):
    """
    SamTrans has a set of Excel files broken down by date ranges.
    Save each as parquet, check it into GCS with upload script
    """
    for filename in list_of_files:
        df = pd.read_excel(
            f"{LOCAL_FOLDER}{agency_name}/{filename}", engine="openpyxl"
        )
            
        int_cols_type = [
            "Run", "Schedule", "Vehicle", "Sequence", "Stop ID", 
            "Ons", "Offs", "Pos Src", "Qual Ind", "Num Sat"
        ]
        df[int_cols_type] = df[int_cols_type].astype("Int64")
        df["APC Date"] = pd.to_datetime(df["APC Date"])

        df.to_parquet(
            f"{AGENCY_GCS}{agency_name}/{Path(filename).stem}.parquet",
            filesystem = gcsfs.GCSFileSystem()     
        )
        print(f"exported {filename} as parquet")
    
    return 

def ingest_samtrans(
    agency_name: str = "samtrans"
) -> pd.DataFrame:
    """
    1. Combine files into one dataset
    2. Aggregate trip-stop to stop level ridership.
    3. There are cases where stop name strings are diff but they are the same stop 
    because of the dot in the street type, 
    for example, "3rd Ave & Pint St" vs "3rd Ave & Pine St.". 
    Standardize the stop names (keep the version without the dot).

    Note: The data is for each trip-stop, including door open and close time. 
    The lat and lon at the same stop can be slightly different across trips. 
    The agg in the preprocessing takes maximum of the lat and lon for each 
    stop across trips, routes and dates.
    """
    list_of_files = list(RAW_DATA_YAML[agency_name])

    # Export Excel as parquets first
    export_excel_as_parquet(agency_name, list_of_files)

    # Read in parquet and concatenate together as df to do further filtering
    raw_samtrans = pd.concat([
        pd.read_parquet(
            f"{AGENCY_GCS}{agency_name}/{Path(filename).stem}.parquet",
        ) for filename in list_of_files
    ], axis=0, ignore_index=True)
 
    raw_samtrans = raw_samtrans[~raw_samtrans["Route"].str.startswith(("Applied filters"), na=False)]

    raw_samtrans_agg = (
        raw_samtrans
        .groupby(["Route", "APC Date", "Stop ID", "Stop Name"], dropna=False)
        .agg({"Ons": "sum", "Offs": "sum"})
        .reset_index()
    )

    # could coerce as gdf and dedupe too
    stop_loc_map = (
        raw_samtrans
        .groupby(["Stop ID", "Stop Name"], dropna=False)
        .agg({"Lat": "max", "Lon": "max"})
        .reset_index()
    )
    
    raw_samtrans_export = pd.merge(
        raw_samtrans_agg, 
        stop_loc_map, 
        on=["Stop ID", "Stop Name"], 
        how="left"
    )
    
    raw_samtrans_export = raw_samtrans_export.assign(
        day_type = pd.to_datetime(raw_samtrans_export["APC Date"]).apply(time_utils.get_day_type),
        start_date = pd.to_datetime(raw_samtrans["APC Date"]),
        end_date = pd.to_datetime(raw_samtrans["APC Date"]),
        schedule_name = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    )
    
    return raw_samtrans_export

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
        "Stop ID": "stop_id",
        "Stop Name": "stop_name",
        "Lat": "stop_lat",
        "Lon": "stop_lon",
        "Ons": "avg_boardings",
        "Offs": "avg_alightings"
    }
    
    df = df.assign(
        reporting_unit = "day",
        ridership_measure = "daily",
        geography_grain = "trip_stop",
        daily_ridership_basis = "reported_daily"
    ).rename(columns = RENAME_COLS_DICT)
    
    return df
    
if __name__ == "__main__":
   
    agency_name = "samtrans"
  
    raw_samtrans_export = ingest_samtrans(agency_name)
    raw_samtrans_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )
    
    print(f"exported: {agency_name}")
