"""
Santa Cruz Metro

1. Combine four files to one dataset
2. Extract date information from file names
3. Hard code start date and end date for the FY2025 (2024-07-01 to 2025-06-30)
4. Format stop name and agg/sum ridership for the same stop. E.g., "Barack Obama Blvd + W San Carlos" and "Barack Obama Blvd + W San Carlos [0901]".
5. stop id 2594 has two diff stop names: Freedom Blvd (K-Mart) and Freedom Blvd (Vallarta Supermarkets). 
stop id 1796: "Soquel Ave + Pacheco Ave" and "Soquel Ave + San Juan Ave" stop id 1666: "Ocean + Hubbard " 
and "Ocean + Washburn Ave" We could make the name consistent (keep the first one), but for now, keep both since stop name may change over time.
"""
import gcsfs
import pandas as pd

import time_utils
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def flatten_columns_scm(columns: list) -> list:
    """Flatten a multi-index of two header rows into single column names."""
    
    new_cols = []
    for top, bottom in columns:
        top = str(top).strip() if pd.notna(top) else ""
        bottom = str(bottom).strip() if pd.notna(bottom) else ""
        
        if bottom.startswith("Unnamed"):
            bottom = ""
        if bottom and bottom != top:
            name = f"{top} {bottom}".strip()
        else:
            name = top
            
        new_cols.append(name)
    
    return new_cols


def clean_individual_excel(filename: str):
    """
    For each individual Excel workbook, grab the rows we need,
    aggregate boardings and aligtings, add a column to designate the file it came from. 
    """
    raw_scm = pd.read_excel(
        f"{LOCAL_FOLDER}{agency_name}/{filename}", 
        header=[0,1], engine="openpyxl"
    )
    raw_scm.columns = flatten_columns_scm(raw_scm.columns)
    
    raw_scm = raw_scm[~raw_scm["Stop Name"].str.startswith(("Total", "Minimum", "Maximum", "Average", "Std. Dev."), na=False)]
	
    raw_scm["filename"] = filename
    raw_scm["Stop Name"] = raw_scm["Stop Name"].str.replace(r"\s*\[.*$", "", regex=True).str.strip()
	
    raw_scm_grouped = raw_scm.groupby(
        by=["Stop Name", "Stop ID", "filename"], 
        as_index=False, dropna=False
    ).agg({
        "Boardings": "sum", 
        "Alightings": "sum"
    }).reset_index()

    return raw_scm_grouped


def ingest_santa_cruz_metro(
    agency_name: str = "santa_cruz_metro",
) -> pd.DataFrame:
    """
    """
    list_of_files = list(RAW_DATA_YAML[agency_name])

    list_of_cleaned_dfs = [clean_individual_excel(one_filename) for one_filename in list_of_files]
    raw_scm_export = pd.concat(list_of_cleaned_dfs, axis=0, ignore_index=True)

    start_date, end_date = time_utils.get_fiscal_year_range(2025, 7)
    
    raw_scm_export = raw_scm_export.assign(
        start_date = pd.to_datetime(start_date),
        end_date = pd.to_datetime(end_date),
        schedule_name = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    )

    raw_scm_export = raw_scm_export.groupby(
        by=["Stop Name", "Stop ID", "start_date", "end_date", "schedule_name"], dropna=False
    ).agg({
        "Boardings": "sum", 
        "Alightings": "sum"
    }).reset_index()

    return raw_scm_export
    

if __name__ == "__main__":
   
    agency_name = "santa_cruz_metro"
    
    raw_scm_export = ingest_santa_cruz_metro(agency_name)
    raw_scm_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")