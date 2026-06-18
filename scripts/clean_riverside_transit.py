"""
Riverside Transit

Note: The original raw datasets are transactions data,
which are too large to directly upload to Github.

- Filtered transactions df is exported as parquet.
- Transactions aggregated to stop ridership is exported as parquet.
"""

import gcsfs
import pandas as pd
import time_utils
from shared_vars import AGENCY_TO_GTFS_NAME_DICT, LOCAL_FOLDER, RAW_DATA_YAML, RAW_GCS


def aggregate_transactions_to_ridership(transactions_df: pd.DataFrame) -> pd.DataFrame:
    """
    extract only valid transaction types
    (values not in the list are the meta data rows)
    """
    ridership_transaction_codes = [
        "114 - Stored ride card",
        "115 - Period pass",
        "119 - Got fare",
        "129 - Special card",
        "212 - Mobile Ticket Transaction",
    ]

    raw_riverside = transactions_df[transactions_df["Transaction Type"].isin(ridership_transaction_codes)]

    raw_riverside["date"] = pd.to_datetime(raw_riverside["Date Time"], errors="coerce").dt.date
    raw_riverside["date"] = pd.to_datetime(raw_riverside["date"], errors="coerce")

    raw_riverside_export = (
        raw_riverside.groupby(["date", "Stop ID", "Route", "Direction"], as_index=False, dropna=False)
        .agg({"Stop ID": "count", "Longitude": "max", "Latitude": "max"})
        .rename(columns={"Stop ID": "ridership"})
    )

    return raw_riverside_export


def filter_transactions(filename: str) -> pd.DataFrame:
    """
    Find the index of the first "Search Criteria" row and drop all
    following rows which are not ridership data.
    Clean up the filtered transactions to get ridership
    """
    t_raw_df = pd.read_csv(filename, header=4)

    first_col = t_raw_df.columns[0]
    mask = t_raw_df[first_col].astype(str).str.contains("Search Criteria")
    if mask.any():
        cutoff_idx = mask.idxmax()
        t_raw_df = t_raw_df.loc[: cutoff_idx - 1]
    
    # Coerce dtypes here because we're saving out filtered transactions too.
    # these dtypes should match what we'll use for transactions -> stop ridership
    t_raw_df = t_raw_df.astype({"Route": "Int64", "Stop ID": "Int64"})

    t_raw_df["Location"] = pd.to_numeric(t_raw_df["Location"], errors='coerce'i
    t_raw_df['Location'] = t_raw_df['Location'].astype('Int64')

    # Convert mixed string formats into datetime dtype (1/1/2025 00:00 an 01/01/2025 00:00:00 will be converted to consistent format)
    t_raw_df["Date Time"] = pd.to_datetime(t_raw_df["Date Time"], errors="coerce", format="mixed")

    return t_raw_df


def ingest_riverside_transit(agency_name: str = "riverside_transit") -> pd.DataFrame:
    """
    Aggregate swipe/transaction level data to stop level ridership.

    Filtered transactions are saved as parquet.

    Preprocess the raw data and aggregate to stop level ridership.
    Lat and lon for each (stop, route, direction) are the max/min of all
    records for the corresponding combination.
    """
    list_of_files = list(RAW_DATA_YAML[agency_name])

    filtered_raw_transactions = pd.concat(
        [filter_transactions(f"{LOCAL_FOLDER}{agency_name}/{filename}") for filename in list_of_files],
        axis=0,
        ignore_index=True,
    )

    # this needs to be uploaded too
    filtered_raw_transactions.to_parquet(
        f"{RAW_GCS}{agency_name}/filtered_transactions_round1.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    raw_riverside_export = aggregate_transactions_to_ridership(filtered_raw_transactions)
    raw_riverside_export["start_date"] = raw_riverside_export["date"]
    raw_riverside_export["end_date"] = raw_riverside_export["date"]
    raw_riverside_export["day_type"] = raw_riverside_export["date"].apply(time_utils.get_day_type)
    raw_riverside_export["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]

    return raw_riverside_export


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
        "Stop ID": "stop_id",
        "Stop Name": "stop_name",
        "Route": "route_id",
        "Direction": "direction",
        "Longitude": "stop_lon",
        "Latitude": "stop_lat",
        "ridership": "avg_ridership",
    }

    df = df.assign(
        reporting_unit="day",
        ridership_measure="",
        geography_grain="transaction",
        daily_ridership_basis="derived_from_transactions",
    ).rename(columns=RENAME_COLS_DICT)

    return df


if __name__ == "__main__":

    agency_name = "riverside_transit"
    raw_riverside_export = ingest_riverside_transit(agency_name)
    raw_riverside_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")
