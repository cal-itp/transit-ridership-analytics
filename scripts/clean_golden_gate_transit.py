"""
Golden Gate Transit
Aggregate to stop level. The raw data has trip-stop grain.
"""
import gcsfs
import pandas as pd

import time_utils
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_golden_gate_transit(
    agency_name: str = "golden_gate_transit",
) -> pd.DataFrame:
    """
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
    

if __name__ == "__main__":
   
    agency_name = "golden_gate_transit"
    
    raw_ggt_export = ingest_golden_gate_transit(agency_name)
    raw_ggt_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")