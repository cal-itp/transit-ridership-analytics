"""
Gold Coast Transit

1. Import one sheet (May 2025 data) for now, which contains most comprehensive columns/info.
2. Add headers/column names.
"""
import gcsfs
import pandas as pd
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_gold_coast_transit(
    agency_name: str = "gold_coast_transit",
    sheet_name: str = "May_2025_Stop_Ridership"
) -> pd.DataFrame:
    """
    """
    filename = RAW_DATA_YAML[agency_name][0]
    
	# specify headers (inferred from other sheets from the same excel)
    headers = [
        'day_of_week', 'route', 'direction', 'stop_id', 'unknown', 'stop_name', 'total_on', 'total_off', 
        'total_activity', 'cumulative_load', 'lat', 'lon'
    ]
    # .xls needs a different engine
    raw_gct = pd.read_excel(
	    f"{LOCAL_FOLDER}{agency_name}/{filename}", 
        sheet_name=sheet_name, header=None, names=headers,
        engine="xlrd", 
	).reset_index(drop=True)

    raw_gct_export = raw_gct.assign(
        start_date = pd.to_datetime('2025-05-01'),
        end_date = pd.to_datetime('2025-05-31'),
        schedule_name = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    ).astype({
        "route": "str", # this gave error with parquet export because some looked like int
        "unknown": "int"# this might be stop_sequence
    })

    return raw_gct_export
    

if __name__ == "__main__":
   
    agency_name = "gold_coast_transit"
    
    raw_gct_export = ingest_gold_coast_transit(agency_name)
    raw_gct_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")