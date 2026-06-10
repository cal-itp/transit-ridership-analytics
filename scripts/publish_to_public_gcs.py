"""
Export the final ridership dataset to public GCS bucket:
- geoparquet
- zipped geojson
- csv (zipped and unzipped)

GTFS Digest example: https://github.com/cal-itp/data-analyses/blob/1965922d4c98dbb9b2f64dba1691dd3c57680551/gtfs_digest/_publish_public_data.py
"""
import geopandas as gpd
import google.auth
import gcsfs
import pandas as pd

from pathlib import Path
from typing import Literal

from ridership_utils import publish_utils, utils
#from shared_vars import PROCESSED_GCS, PUBLIC_GCS

GCS_FILE_PATH = "gs://calitp-analytics-data/data-analyses/transit-ridership-analytics/"
INTERMED_GCS = f"{GCS_FILE_PATH}intermediate/"
PROCESSED_GCS = f"{GCS_FILE_PATH}processed/"
PUBLIC_GCS = "gs://calitp-publish-data-analysis/"

credentials, _ = google.auth.default()

    
def export_gdf_to_gzip_geojson(
    gdf: gpd.GeoDataFrame,
    export_filename: str
):
    """
    Convert gdf to gzipped geojson.
    Datetime columns must be coerced to string.
    Geometry is ok.
    """
    # geojson can't do timestamps, so must coerce to string
    date_cols = gdf.select_dtypes("datetime64").columns
    geojson_bytes = gdf.astype({c: "str" for c in date_cols}).to_json().encode("utf-8")
	
    with gcsfs.GCSFileSystem().open(export_filename, "wb") as writer:
        with gzip.GzipFile(fileobj=writer, mode="w") as gz:
            gz.write(geojson_bytes)

    print(f"exported {export_filename}")
	
    return 

def export_parquet_as_csv_geojson(
    df: gpd.GeoDataFrame,
    export_folder: str,
    filename: str,
    filetype: Literal["csv", "geojson"]
):
    """
    """
    date_cols = df.select_dtypes("datetime64").columns

    if filetype=="csv":

        # back out geometry into stop_lon / stop_lat
        # coerce dtypes as best as possible here
        df = df.assign(
            stop_lon = df.geometry.x,
            stop_lat = df.geometry.y
        ).drop(
            columns = ["geometry"]
        ).astype({c: "str" for c in date_cols})

        df.to_csv(
            f"{export_folder}{Path(filename).stem}.csv", index=False
        )
        
    elif filetype=="geojson":
        df = df.astype({c: "str" for c in date_cols})

        utils.geojson_gcs_export(
            df,
            f"{export_folder}",
            Path(filename).stem,
            geojson_type = "geojson"
        )

        
        
if __name__ == "__main__":
    
	gdf = gpd.read_parquet(
	    f"{INTERMED_GCS}dim_stops_with_feed_service_period.parquet",
	    storage_options={"token": credentials.token}
	)
	
	#export_gdf_to_gzip_geojson(gdf, f"{PROCESSED_GCS}publish/test.gzip")
	
	export_parquet_as_csv_geojson(
		gdf, 
		export_folder = f"{PROCESSED_GCS}publish/", 
		filename = "test.csv",
		filetype = "csv"
	)

	export_parquet_as_csv_geojson(
		gdf, 
		export_folder = f"{PROCESSED_GCS}publish/", 
		filename = "test",
		filetype = "geojson"
	)
    
	'''
	# copy our private files to public GCS
	# make sure we can stage files ready to publish and double check first
	filepaths = [
		f"{PROCESSED_GCS}publish/test.gzip",
		f"{PROCESSED_GCS}publish/test.geoparquet",
		f"{PROCESSED_GCS}publish/test.csv"
	]
	
	for f in filepaths:
        publish_utils.write_to_public_gcs(
            f,
            f"transit_ridership/{Path(f).name}",
            PUBLIC_GCS
        )
	'''