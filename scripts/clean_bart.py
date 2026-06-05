"""
BART
Reformat data from wide to long format.
Join raw data and station crosswalk tables to get full station name.
"""
import gcsfs
import pandas as pd
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_bart_entries_and_exits(
    agency_name: str = "bart",
    sheet_name: str = "Daily Raw Data"
) -> pd.DataFrame:
    """
    Import BART entries and exit Excel and clean up columns.
    """
    filename = RAW_DATA_YAML[agency_name][0]
    raw_bart = pd.read_excel(
        f"{LOCAL_FOLDER}{agency_name}/{filename}", sheet_name=sheet_name, header=[0,1],
		engine="openpyxl"
    )
	
    # get level 1 and level 2 headers
    top_headers = raw_bart.columns.get_level_values(0)
    bottom_headers  = raw_bart.columns.get_level_values(1)

    # identify metadata columns and ridership columns (entries/exits)
    meta_cols = [c for c, top in zip(raw_bart.columns, top_headers) if "Unnamed" in str(top)]
    ridership_cols = [c for c, top in zip(raw_bart.columns, top_headers) if ("Exits"  in str(top)) or ("Entries" in str(top))]

    # melt ridership columns
    t_df_ridership = raw_bart.melt(
        id_vars=meta_cols, value_vars=ridership_cols, value_name="ridership"
    ).rename(
        columns={
            "variable_0": "type",
            "variable_1": "Station"
        }
    )

    # pivot table
    t_df_ridership_pivot = t_df_ridership.pivot_table(
        index=meta_cols+["Station"],
        columns="type",
        values="ridership",
        aggfunc="sum"
    ).reset_index()
    
    t_df_ridership_pivot.columns = [
		bottom_headers[i] 
		if i < len(meta_cols) else t_df_ridership_pivot.columns[i] 
        for i in range(len(t_df_ridership_pivot.columns))
	]

    return t_df_ridership_pivot


def ingest_bart_station_crosswalk(
    agency_name: str = "bart",
    sheet_name: str = "Station Crosswalk"
) -> pd.DataFrame:
    """
    Import station crosswalk Excel 
    to get the full station name.
    """
    filename = RAW_DATA_YAML[agency_name][0]
    
    raw_bart_station = pd.read_excel(
        f"{LOCAL_FOLDER}{agency_name}/{filename}", 
		sheet_name=sheet_name, 
		engine="openpyxl"
    )
    raw_bart_station.columns = ["Station Code", "Station Name"]

    return raw_bart_station


def merge_bart_entries_exits_station(
    entries_df: pd.DataFrame,
    station_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join raw data and station crosswalk tables to get full station name.
    """
    # add station name
    raw_bart_export = pd.merge(
        entries_df, 
        station_df, 
        how="left", 
        left_on="Station", 
        right_on="Station Code"
    ).drop(
		columns="Station Code"
	).astype({"Station": "str"})
    
    # add date range, columns needed, coerce dtypes
    raw_bart_export = raw_bart_export.assign(
        start_date = pd.to_datetime(raw_bart_export.Date),
        end_date = pd.to_datetime(raw_bart_export.Date),
        schedule_name = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    )

    return raw_bart_export
    
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
        "Day Type": "day_type",
        "Station Name": "stop_name",
        "Entries": "avg_boardings",
        "Exits": "avg_alightings"
    }
    
    df = df.assign(
        reporting_unit = "day",
        ridership_measure = "daily",
        geography_grain: "stop",
        daily_ridership_basis = "reported_daily"
    ).rename(columns = RENAME_COLS_DICT)
    
    return df
    
if __name__ == "__main__":
    
    agency_name = "bart"   
	
    t_df_ridership_pivot = ingest_bart_entries_and_exits(agency_name)
    raw_bart_station = ingest_bart_station_crosswalk(agency_name)
    
    raw_bart_export = merge_bart_entries_exits_station(t_df_ridership_pivot, raw_bart_station)
    raw_bart_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")