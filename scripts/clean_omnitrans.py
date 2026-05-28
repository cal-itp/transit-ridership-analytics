"""
OmniTrans

Average to daily. Raw data is total ridership over each fiscal year.
Add date according to fiscal year, i.e., first day of the fiscal year.
Note: For each Stop Name, there can be multiple rows. Need to first sum up for stop name then divided by 365 to get day avg.
"""
import calendar
import gcsfs
import pandas as pd

import time_utils
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_omnitrans(
    agency_name: str = "omnitrans",
) -> pd.DataFrame:
    """
    """
    filename = RAW_DATA_YAML[agency_name][0]
    
    raw_omni = pd.read_excel(
	    f"{LOCAL_FOLDER}{agency_name}/{filename}", engine="openpyxl", 
	)

    # sum up totals for each stop name
    raw_omni_export = (
        raw_omni.groupby(["FiscalYear", "Route", "Stop Name"], dropna=False)
        [["Total Board", "Total Alight"]]
        .sum()
        .reset_index()
    )

    # avg total ridership of fiscal year
    raw_omni_export["FiscalYear"] = raw_omni_export["FiscalYear"].astype(int)
    raw_omni_export["fiscal_year_days"] = raw_omni_export["FiscalYear"].apply(lambda y: 366 if calendar.isleap(y) else 365)
    raw_omni_export['avg_boardings'] = raw_omni_export['Total Board']/raw_omni_export["fiscal_year_days"]
    raw_omni_export['avg_alightings'] = raw_omni_export['Total Alight']/raw_omni_export["fiscal_year_days"]

    # specify start month of fiscal year
    start_month = 7
    raw_omni_export[["start_date", "end_date"]] = raw_omni_export["FiscalYear"].apply(
        lambda x: pd.Series(time_utils.get_fiscal_year_range(x, start_month)))
    
    raw_omni_export = raw_omni_export.assign(
        start_date = pd.to_datetime(raw_omni_export.start_date),
        end_date = pd.to_datetime(raw_omni_export.end_date),
        day_type = "all",
        schedule_name = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    )
    
    return raw_omni_export
    

if __name__ == "__main__":
   
    agency_name = "omnitrans"
    
    raw_omni_export = ingest_omnitrans(agency_name)
    raw_omni_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")