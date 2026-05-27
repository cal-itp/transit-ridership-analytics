"""
SamTrans

1. Combine files into one dataset
2. Aggregate trip-stop to stop level ridership.
3. There are cases where stop name strings are diff but they are the same stop because of the dot in the street type, 
for example, "3rd Ave & Pint St" vs "3rd Ave & Pine St.". 
Standardize the stop names (keep the version without the dot).

Note: The data is for each trip-stop, including door open and close time. 
The lat and lon at the same stop can be slightly different across trips. 
The agg in the preprocessing takes maximum of the lat and lon for each stop across trips, routes and dates.

Potentially, make stop a gdf here and dedupe and keep as geoparquet. 
Depends how it's used against GTFS in subsequent step.
"""
import gcsfs
import pandas as pd

import time_utils
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_samtrans(
    agency_name: str = "samtrans"
) -> pd.DataFrame:
    """
    """
    list_of_files = list(RAW_DATA_YAML[agency_name])
    raw_samtrans = pd.concat(
        [pd.read_excel(f"{LOCAL_FOLDER}{agency_name}/{filename}", engine="openpyxl")
        for filename in list_of_files], 
        axis=0, ignore_index=True
    )

    int_cols_type = ["Run", "Schedule", "Vehicle", "Sequence", "Stop ID", "Ons", "Offs", "Pos Src", "Qual Ind", "Num Sat"]
    raw_samtrans[int_cols_type] = raw_samtrans[int_cols_type].astype("Int64")
    raw_samtrans["APC Date"] = pd.to_datetime(raw_samtrans["APC Date"])     
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
    

if __name__ == "__main__":
   
    agency_name = "samtrans"
  
    raw_samtrans_export = ingest_samtrans(agency_name)
    raw_samtrans_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )
    
    print(f"exported: {agency_name}")