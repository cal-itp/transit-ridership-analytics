"""
"""
import geopandas as gpd
import gcsfs
import google.auth
import pandas as pd

from google.cloud import bigquery

import time_utils
from shared_vars import RAW_GCS, INTERMED_GCS, RAW_DATA_YAML
from ridership_utils import geography_utils, bq_utils, utils

credentials, project = google.auth.default()

def download_schedule_feeds(filename: str):
    """
    From mart_gtfs.fct_daily_feed_scheduled_service_summary, 
    group by feed_key and gtfs_dataset_name to find the relevant
    service_date date range. 
    
    Save this as a parquet.

    TODO: what should argument be? don't want this query to run
    """
    sql_query = f"""
        SELECT
            feed_key,
            gtfs_dataset_name AS schedule_name,
            MIN(service_date) AS service_date_start,
            MAX(service_date) AS service_date_end,
        FROM `cal-itp-data-infra.mart_gtfs.fct_daily_feed_scheduled_service_summary`
        WHERE service_date >= "2023-01-01" -- maybe, if we really want to filter
        GROUP BY 1, 2
    """

    df = bq_utils.bq_faster_download(sql_query)
        
    df = df.astype({
        "service_date_start": "datetime64[ns]",
        "service_date_end": "datetime64[ns]"
    })

    df.to_parquet(
        f"{INTERMED_GCS}{filename}.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(df.shape)
    print("saved schedule feeds")
    
    return 


def download_dim_stops_for_feeds_present(
    subset_feeds: list
):
    keep_stop_cols = [
        "key",
        "feed_key",
        "stop_id",
        "stop_name",
        "stop_code",
        "pt_geom",
    ]

    basic_sql_query = bq_utils.basic_sql_query(
        project_name = "cal-itp-data-infra", 
        dataset_name = "mart_gtfs",
        table_name = "dim_stops", 
        columns = keep_stop_cols
    )
    
    query_params = bq_utils.set_bq_query_params(
        array_query_parameter = {"feed_key": subset_feeds},
    )
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=query_params
    )
    
    sql_query = f"{basic_sql_query} WHERE feed_key IN UNNEST(@feed_key)"
    
    print(f"query: {sql_query}")
    print(f"job_config: {job_config}")
    
    df = bq_utils.bq_faster_download(sql_query, job_config=job_config)
    
    df = geography_utils.convert_to_gdf(df, "pt_geom", "point")

    utils.geoparquet_gcs_export(
        df,
        INTERMED_GCS,
        "dim_stops_round1"
    )

    print("exported dim_stops")
    
    return 

def get_ridership_start_and_end(list_of_operators: list) -> pd.DataFrame: 

    operators_with_ridership = pd.concat([
        pd.read_parquet(
            f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
            columns = ["schedule_name", "start_date", "end_date"],
            filesystem = gcsfs.GCSFileSystem()
        ) for agency_name in list_of_operators
        ], axis=0, ignore_index=True
    ).drop_duplicates().reset_index(drop=True)

    # for each operator, get only 1 ridership start / end date
    operator_ridership_period = (
        operators_with_ridership
        .groupby("schedule_name")
        .agg({
            "start_date": "min",
            "end_date": "max"
        })
        .reset_index()
        .rename(columns = {
            "start_date": "ridership_start_date",
            "end_date": "ridership_end_date"
        })
    )

    return operator_ridership_period

def merge_feeds_with_ridership_period(
    feeds_df: pd.DataFrame,
    operator_ridership_period_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    """
    operator_feeds = pd.merge(
        operator_ridership_period_df,
        feeds_df,
        on = "schedule_name",
        how = "inner"
    ).sort_values(["schedule_name", "service_date_start"]).reset_index(drop=True)

    # calculate_time_overlap is a row-wise function
    operator_feeds["overlap_days"] = operator_feeds.apply(
        lambda x: 
        time_utils.calculate_time_overlap(
            x.service_date_start, x.service_date_end,
            x.ridership_start_date, x.ridership_end_date), axis=1)

    filtered_operator_feeds = operator_feeds[
        operator_feeds.overlap_days > 0
    ].reset_index(drop=True)
    
    return filtered_operator_feeds

if __name__ == "__main__":

    SCHEDULE_FEEDS_FILENAME = "schedule_feeds"
    #download_schedule_feeds(SCHEDULE_FEEDS_FILENAME)

    feeds_df = pd.read_parquet(
        f"{INTERMED_GCS}{SCHEDULE_FEEDS_FILENAME}.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )
    
    list_of_operators = list(RAW_DATA_YAML.keys())

    # Grab the ridership start/end from all the individual operator parquets
    ridership_df = get_ridership_start_and_end(list_of_operators)

    # Merge this with all schedule feeds, filter to any active feed during ridership period
    filtered_feeds_df = merge_feeds_with_ridership_period(feeds_df, ridership_df)
    feeds_present = filtered_feeds_df.feed_key.unique().tolist()

    # download dim_stops for these feed_keys
    download_dim_stops_for_feeds_present(feeds_present)



    