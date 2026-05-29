"""
"""
import geopandas as gpd
import gcsfs
import pandas as pd

from google.cloud import bigquery

from shared_vars import INTERMED_GCS
from ridership_utils import geography_utils, bq_utils, utils


def download_schedule_feeds(filename: str):
    """
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


def download_dim_stops(subset_feeds: list) -> gpd.GeoDataFrame:
    """
    Download dim_stops and convert to gdf
    """
    # this doesn't parse correctly yet
    feed_keys_string = bq_utils.list_of_strings_as_string(list_of_feed_keys)

    
    keep_stop_cols = [
        "key",
        "feed_key",
        "stop_id",
        "stop_name",
        "stop_code",
        "pt_geom",
    ]

    subset_columns_string = bq_utils.list_as_string(keep_stop_cols)
    sql_query = f"""
        SELECT {subset_columns_string}
        FROM `cal-itp-data-infra.mart_gtfs.dim_stops`
    """
    df = bq_utils.bq_faster_download(sql_query)
    df = geography_utils.convert_to_gdf(df, "pt_geom", "point")

    
    '''
    dim_stops = bq_utils.download_table_custom_filter(
        project_name = "cal-itp-data-infra",
        dataset_name = "mart_gtfs",
        table_name = "dim_stops",
        date_col = None,
        columns = keep_stop_cols,
        geom_col = "pt_geom",
        geom_type = "point",
    )
    '''
    utils.geoparquet_gcs_export(
        df,
        INTERMED_GCS,
        "dim_stops"
    )

    print("saved dim_stops")
    
    return

if __name__ == "__main__":

    SCHEDULE_FEEDS_FILENAME = "schedule_feeds"
    #download_schedule_feeds(SCHEDULE_FEEDS_FILENAME)

    list_of_feed_keys = pd.read_parquet(
        f"{INTERMED_GCS}{SCHEDULE_FEEDS_FILENAME}.parquet",
        columns = ["feed_key"],
        filesystem = gcsfs.GCSFileSystem()
    ).feed_key.unique().tolist()

    download_dim_stops(list_of_feed_keys)
    

    