"""
Long Beach Transit
"""
import gcsfs
import pandas as pd

import time_utils
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_long_beach_transit(
    agency_name: str = "long_beach_transit",
) -> pd.DataFrame:
    """
    Import Long Beach Excel.
    """
    filename = RAW_DATA_YAML[agency_name][0]
    
    raw_long_beach = pd.read_excel(
	    f"{LOCAL_FOLDER}{agency_name}/{filename}", engine="openpyxl", 
	)

    raw_long_beach_export = raw_long_beach.groupby(
        by=['DayType', 'Route', 'Direction', 'StopID', 'StopName'], dropna=False
    )[['Boardings', 'Alightings']].sum().reset_index()
    
    fiscal_year = 2025
    start_month = 7
    start_date, end_date = time_utils.get_fiscal_year_range(fiscal_year, start_month)

    raw_long_beach_export = raw_long_beach_export.assign(
        start_date = pd.to_datetime(start_date),
        end_date = pd.to_datetime(end_date),
        schedule_name = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    )
    
    return raw_long_beach_export
    
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
        "DayType": "day_type",
        "Route": "route_id",
        "Direction": "direction",
        "StopID": "stop_id",
        "StopName": "stop_name",
        "Boardings": "avg_boardings",
        "Alightings": "avg_alightings"
    }

    df = df.assign(
        reporting_unit = "fiscal_year",
        ridership_measure = "avg_daily",
        geography_grain = "stop",
        daily_ridership_basis = "reported_avg_daily"
    ).rename(columns = RENAME_COLS_DICT)
    
    return df
    
if __name__ == "__main__":
   
    agency_name = "long_beach_transit"
    
    raw_long_beach_export = ingest_long_beach_transit(agency_name)
    raw_long_beach_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")