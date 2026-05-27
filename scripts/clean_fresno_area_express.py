"""
Fresno Area Express (City of Fresno) 
  script is called clean_fresno_area_express (change yaml), 
  but yaml change to Fresno Area Express would be more descriptive and follow how 
  other folders describe transit agencies, not organizations (could be city).
  the exported Excel was named Fresno Area Express, indicating this is the folder to use.
Add day type, start and end date column to fit in staging table schema.
"""
import gcsfs
import pandas as pd

import time_utils
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_fresno_area_express(
    agency_name: str = "fresno_area_express"
) -> pd.DataFrame:
    """
    """
    filename = RAW_DATA_YAML[agency_name][0]
    raw_fresno = pd.read_excel(f"{LOCAL_FOLDER}{agency_name}/{filename}", engine="openpyxl")

    raw_fresno_export = raw_fresno.groupby(
        by=["Date", "StopID", "StopLabel"], dropna=False
    )[["ProjectedBoarding", "ProjectedAlighting"]].sum().reset_index()
    
    raw_fresno_export["start_date"] = pd.to_datetime(raw_fresno_export["Date"])
    raw_fresno_export["end_date"] = pd.to_datetime(raw_fresno_export["Date"])
    raw_fresno_export["day_type"] = raw_fresno_export["Date"].apply(time_utils.get_day_type)
    raw_fresno_export["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    
    return raw_fresno_export

	
if __name__ == "__main__":
   
    agency_name = "fresno_area_express"
  
    raw_fresno_export = ingest_fresno_area_express(agency_name)
    raw_fresno_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )
    
    print(f"exported: {agency_name}")