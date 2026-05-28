"""
Big Blue Bus
Add start and end date of service period/aggregation period.
Note: Each stop id can have more than 1 record.
"""
import gcsfs
import pandas as pd
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_big_blue_bus(
    agency_name: str = "big_blue_bus"
) -> pd.DataFrame:
    """
    """
    filename = RAW_DATA_YAML[agency_name][0]
    raw_big_blue_bus = pd.read_excel(
		f"{LOCAL_FOLDER}{agency_name}/{filename}", engine="openpyxl"
	)
    raw_big_blue_bus_export = raw_big_blue_bus.groupby(
        ["SERVICE_PERIOD", "SERVICE_DAY", "ROUTE_NUMBER", "ROUTE_NAME", "DIRECTION_NAME",
        "STOP_ID", "STOP_NAME", "STOP_LAT", "STOP_LON"], dropna=False
    )[["AVERAGE_DAILY_BOARDINGS", "AVERAGE_DAILY_ALIGHTINGS"]].sum().reset_index()

    raw_big_blue_bus_export["start_date"] = raw_big_blue_bus_export["SERVICE_PERIOD"]
    raw_big_blue_bus_export["end_date"] = raw_big_blue_bus_export["SERVICE_PERIOD"] + pd.offsets.MonthEnd(4)
    raw_big_blue_bus_export["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    
    return raw_big_blue_bus_export
    

if __name__ == "__main__":
   
    agency_name = "big_blue_bus"
    raw_big_blue_bus_export = ingest_big_blue_bus(agency_name)
    raw_big_blue_bus_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )
	
    print(f"exported: {agency_name}")