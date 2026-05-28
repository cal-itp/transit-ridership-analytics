"""
"""
import gcsfs
import pandas as pd

from google.cloud import bigquery

from shared_vars import INTERMED_GCS
from ridership_utils import bq_utils


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

if __name__ == "__main__":
    
    filename = "schedule_feeds"
    download_schedule_feeds(filename)