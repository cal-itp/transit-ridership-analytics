"""
Golden Gate Park Shuttle
"""
import gcsfs
import pandas as pd
import re
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_golden_gate_park_shuttle(
    agency_name: str = "golden_gate_park_shuttle",
) -> pd.DataFrame:
    """
    Import Golden Gate Park Excel.
    1. Reshape the data from a wide format, where each stop is a separate column, 
    into a long format where each row represents the ridership for a specific 
    stop on a specific day.
    2. Filter out Stop = "Total"
    """
    filename = RAW_DATA_YAML[agency_name][0]
    
    raw_ggp = pd.read_excel(
	    f"{LOCAL_FOLDER}{agency_name}/{filename}", 
        header=None, engine="openpyxl", 
	)
    
    # extract first four column names from the second row (index=1)
    first_four_cols = raw_ggp.iloc[1, 0:4].tolist()
    
    # extract stop names from the firs row starting from 5th row
    stop_names = raw_ggp.iloc[0, 4:].tolist()
    
    # extract data starting from 3rd row
    data_ggp = raw_ggp.iloc[2:, :].copy()
    data_ggp.columns = first_four_cols + stop_names
    
    # convert from wide to long format
    raw_ggp_export = data_ggp.melt(id_vars=first_four_cols, var_name="Stop", value_name="Ridership")
    
    raw_ggp_export = raw_ggp_export.assign(
        start_date = pd.to_datetime(raw_ggp_export["Date"]),
        end_date = pd.to_datetime(raw_ggp_export["Date"]),
        direction = raw_ggp_export["Stop"].str.extract(r"\b([EWSN]\s*B)\b",flags=re.IGNORECASE),
        schedule_name = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    ).dropna(subset="Date").query('Stop != "Total"')
    
    return raw_ggp_export
    
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
        "Date": "date",
        "stop": "stop_name",
        "ridership": "avg_ridership"
    }
    
    df = df.assign(
        reporting_unit = "day",
        ridership_measure = "daily",
        geography_grain = "stop",
        daily_ridership_basis = "reported_daily"
    ).rename(columns = RENAME_COLS_DICT)
    
    return df
    
if __name__ == "__main__":
   
    agency_name = "golden_gate_park_shuttle"
    
    raw_ggp_export = ingest_golden_gate_park_shuttle(agency_name)
    raw_ggp_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")