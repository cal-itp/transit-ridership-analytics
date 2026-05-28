"""
Santa Barbara Metropolitan Transit District
1. Reformat to long format
2. Average from monthly to daily
"""
import gcsfs
import pandas as pd
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def process_individual_sheet(
    filename: str,
    sheet_name: str
) -> pd.DataFrame:
    """
    """
    t_df_sbmtd = pd.read_excel(filename, sheet_name=sheet_name, header=2, engine="openpyxl")
    
    # drop "Grand Total" col, and "Total" row
    t_df_sbmtd = t_df_sbmtd.loc[:, ~t_df_sbmtd.columns.str.contains("Grand Total", case=False, na=False)]
    t_df_sbmtd = t_df_sbmtd[~t_df_sbmtd.iloc[:, 0].astype(str).str.strip().str.lower().eq("total")]

    # identify stop id and stop name cols and month cols
    id_cols = t_df_sbmtd.columns[:2].tolist()
    month_cols = t_df_sbmtd.columns[2:].tolist()

    # melt into long format
    t_df_sbmtd_long = t_df_sbmtd.melt(id_vars=id_cols, var_name="month_str", value_name=sheet_name)

    # get start and end date for each month
    t_df_sbmtd_long["start_date"] = t_df_sbmtd_long["month_str"].apply(lambda x: x.replace(day=1) if pd.notnull(x) else None)
    t_df_sbmtd_long["end_date"] = t_df_sbmtd_long["month_str"].apply(lambda x: x.replace(day=1) + pd.tseries.offsets.MonthEnd(1) if pd.notnull(x) else None)
    
    t_df_sbmtd_long.columns = t_df_sbmtd_long.columns.str.strip()
    
    return t_df_sbmtd_long
    
    
def ingest_sbmtd(
    agency_name: str = "sbmtd"
) -> pd.DataFrame:
    """
    """
    filename = RAW_DATA_YAML[agency_name][0]
    sheet_names = ["Ridership by Stop_Boardings", "Ridership by Stop_Alightings", "Ridership by Stop_Total Act."]
    t_dfs = [process_individual_sheet(f"{LOCAL_FOLDER}{agency_name}/{filename}", one_sheet_name) for one_sheet_name in sheet_names]

    # merge all three sheets on stop id, stop name and month str
    raw_sbmtd = t_dfs[0]
    for t_df in t_dfs[1:]:
        raw_sbmtd = pd.merge(raw_sbmtd, t_df, on=["Stop ID", "Stop Name", "month_str", "start_date", "end_date"])

    raw_sbmtd["days_in_month"] = pd.to_datetime(raw_sbmtd["start_date"]).dt.days_in_month
    raw_sbmtd["avg_boardings"] = 1.0*raw_sbmtd["Ridership by Stop_Boardings"]/raw_sbmtd["days_in_month"]
    raw_sbmtd["avg_alightings"] = 1.0*raw_sbmtd["Ridership by Stop_Alightings"]/raw_sbmtd["days_in_month"]
    raw_sbmtd["avg_ridership"] = 1.0*raw_sbmtd["Ridership by Stop_Total Act."]/raw_sbmtd["days_in_month"]
    raw_sbmtd["day_type"] = "all"
    raw_sbmtd["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]
    
    return raw_sbmtd
    

if __name__ == "__main__":
   
    agency_name = "sbmtd"
    raw_sbmtd = ingest_sbmtd(agency_name)
    raw_sbmtd.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )
	
    print(f"exported: {agency_name}")