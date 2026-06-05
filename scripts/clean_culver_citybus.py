"""
Culver CityBus

Note: Stop sequence can be different for one stop.
"""
import gcsfs
import pandas as pd
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_culver_citybus(
    agency_name: str = "culver_citybus"
) -> pd.DataFrame:
    """
    Import Culver City.
    1. Skip first row (empty) in csv
    2. Aggregate numbers of each time period of day to get daily level ridership.
    """
    filename = RAW_DATA_YAML[agency_name][0]
    raw_culver_city = pd.read_csv(
        f"{LOCAL_FOLDER}{agency_name}/{filename}", skiprows=[1]
    )

    raw_culver_city_export = (
        raw_culver_city.groupby(
            ['Day Of Week', 'Route', 'Direction', 'Stop ID', 'Stop Name'], dropna=False
        )[['Time Period AVG On', 'Time Period AVG Off']].sum() 
        .reset_index()
        .rename(
            columns={'Time Period AVG On': 'AVG On', 'Time Period AVG Off': 'AVG Off'}
        )
    )
    
    raw_culver_city_export['start_date'] = pd.to_datetime('2025-07-14')
    raw_culver_city_export['end_date'] = pd.to_datetime('2025-08-25')
    
    raw_culver_city_export["route_id"] = raw_culver_city_export["Route"].str.extract(r"^\s*([A-Za-z0-9 ]+?)\s*-\s*")
    
    day_type_map = {
        "1-Weekday": "Weekday",
        "2-Saturday": "Saturday",
        "3-Sunday": "Sunday"
    }
    raw_culver_city_export["day_type"] = raw_culver_city_export["Day Of Week"].map(day_type_map)
    raw_culver_city_export["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]

    return raw_culver_city_export
    
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
        "Day of Week": "day_type",
        "Direction": "direction",
        "Route": "route_name",
        "Stop ID": "stop_id",
        "Stop Name": "stop_name",
        "AVG On": "avg_boardings",
        "AVG Off": "avg_alightings"
    }
    
    df = df.assign(
        reporting_unit = "custom_period",
        ridership_measure = "avg_time_of_day",
        geography_grain: "stop",
        daily_ridership_basis = "reported_avg_daily"
    ).rename(columns = RENAME_COLS_DICT)
    
    return df
    
if __name__ == "__main__":
   
    agency_name = "culver_citybus"
    
    raw_culver_city_export = ingest_culver_citybus(agency_name)
    raw_culver_city_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )