"""
SunLine Transit
Format the data.
"""
import gcsfs
import pandas as pd

import time_utils
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML


def parse_ridership_columns(ridership_columns: list) -> pd.DataFrame:
    """
    """
    meta = []
    for top, mid, bottom in ridership_columns:
        meta.append({
                    "col": (top, mid, bottom),
                    "period": str(top).strip(),
                    "date_range": str(mid).strip(),
                    "metric": str(bottom).strip()
        })
        
    df_meta = pd.DataFrame(meta)
    
    # extract start and end date
    df_meta[['start_date_str', 'end_date_str']] = df_meta['date_range'].str.extract(
        r'(\w+\s*\d{1,2},\s*\d{4})\s*to\s*(\w+\s*\d{1,2},\s*\d{4})'
    )
    df_meta['start_date'] = pd.to_datetime(df_meta['start_date_str'])
    df_meta['end_date'] = pd.to_datetime(df_meta['end_date_str'])
    df_meta['agg_basis'] = df_meta['period'].apply(
        lambda x: 'fiscal year' if isinstance(x, str) and 'FY' in x else 'season'
    )

    return df_meta

def make_sunline_df_long(
    raw_sunline_df: pd.DataFrame,
    ridership_meta_df: pd.DataFrame,
    static_cols: list
) -> pd.DataFrame:
    # loop over ridership metric columns and build long-format rows
    long_frames = []
    
    for row in ridership_meta_df.itertuples():
        col = getattr(row, "col")
        
        t_df_static = raw_sunline_df[static_cols].assign(
            metric = getattr(row, "metric"),
            value = raw_sunline_df[col],
            period = getattr(row, "period"),
            start_date = getattr(row, "start_date"),
            end_date = getattr(row, "end_date"),
            agg_basis = getattr(row, "agg_basis")
        )
        long_frames.append(t_df_static)

    
    t_df_long = pd.concat(long_frames, ignore_index=True)
    
    return t_df_long

def ingest_sunline_transit(
    agency_name: str = "sunline_transit",
) -> pd.DataFrame:
    """
    Clean up multi-index columns for stop.
    For ridership, unpack the 3-lines for column names, 
    add those as columns, and build a long df to export
    """
    filename = RAW_DATA_YAML[agency_name][0]
    
    raw_sunline = pd.read_excel(
	    f"{LOCAL_FOLDER}{agency_name}/{filename}", header=[0,1,2], 
        engine="openpyxl", 
	)
    static_cols = ["Stop ID", "Stop Name", "Latitude", "Longitude", "Route Serves Stop"]
    raw_sunline.columns = [
        static_cols[i] if i < len(static_cols) else raw_sunline.columns[i] 
        for i in range(len(raw_sunline.columns))
    ]

    ridership_cols = ["APC Boards", "APC Alights", "Avg. Boards", "Avg. Alights"]
    ridership_cols_raw = [col for col in raw_sunline.columns if col not in static_cols]
    df_meta = parse_ridership_columns(ridership_cols_raw)
    
    t_df_long = make_sunline_df_long(raw_sunline, df_meta, static_cols)
    
    # pivot ridership metrics into columns
    raw_sunline_export = t_df_long.pivot_table(
        index=["Stop ID", "Stop Name", "Latitude", "Longitude", 
               "Route Serves Stop", "period", "start_date", "end_date", "agg_basis"],
        columns='metric',
        values='value',
       aggfunc='first' # when multiple rows have same index+column values, take the first non-null row
    ).reset_index()

    # all of these have characters that need to be parsed first. then set dtype
    for col in ["APC Alights", "APC Boards", "Avg. Alights", "Avg. Boards"]:
        raw_sunline_export[col] = pd.to_numeric(
                                    raw_sunline_export.apply(
                                        lambda x: str(x[col]).strip().replace('-', '').replace('nan', ''), 
                                        axis= 1)
                                    )
    
    raw_sunline_export = raw_sunline_export.assign(
        day_type = "all",
        schedule_name = AGENCY_TO_GTFS_NAME_DICT[agency_name],
    ).astype({
        # explicitly set dtypes for parquet 
        "Route Serves Stop": "str", # looks like mixed integer and strings, should be string
        "APC Alights": "Int64",
        "APC Boards": "Int64",
        "Avg. Alights": "float",
        "Avg. Boards": "float"
    })
    
    return raw_sunline_export
    

if __name__ == "__main__":
   
    agency_name = "sunline_transit"
    
    raw_sunline_export = ingest_sunline_transit(agency_name)
    raw_sunline_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")