"""
Export the final ridership dataset to private GCS bucket, 
then copy those files to public GCS bucket
- geoparquet
- geojson
- csv (unzipped. if using uploading to repo, then zip)

GTFS Digest example: https://github.com/cal-itp/data-analyses/blob/1965922d4c98dbb9b2f64dba1691dd3c57680551/gtfs_digest/_publish_public_data.py
"""
import geopandas as gpd
import google.auth
import gcsfs
import pandas as pd

from pathlib import Path

from ridership_utils import publish_utils, utils
from shared_vars import INTERMED_GCS, PROCESSED_GCS, PUBLIC_GCS

credentials, _ = google.auth.default()
 

def split_filename_into_folder_and_name(export_filename: str):
    name = Path(export_filename).stem
    gcs_parent_path = export_filename.split(name)[0]
    return gcs_parent_path, name

def export_as_csv(
    gdf: gpd.GeoDataFrame,
    export_filename: str
):
    """
    Export as csv.

    Handle dtypes:
    - back out geometry into stop_lon / stop_lat
    - coerce dtypes as best as possible here
    """
    date_cols = df.select_dtypes("datetime64").columns

    gdf = df.assign(
        stop_lon = gdf.geometry.x,
        stop_lat = gdf.geometry.y
    ).drop(
        columns = ["geometry"]
    ).astype({c: "str" for c in date_cols})


    gcs_parent_path, name = split_filename_into_folder_and_name(export_filename)
    
    gdf.to_csv(
        f"{gcs_parent_path}{name}.csv", index=False
    )
    
    return

def export_as_geojson(
    gdf: gpd.GeoDataFrame,
    export_filename: str,
):
    """
    Export as geojson.
    geojson can't have datetime columns, so coerce to string
    """
    date_cols = df.select_dtypes("datetime64").columns
   
    gdf = df.astype({c: "str" for c in date_cols})
    
    gcs_parent_path, name = split_filename_into_folder_and_name(export_filename)
    
    utils.geojson_gcs_export(
        gdf,
        f"{gcs_parent_path}",
        name,
        geojson_type = "geojson"
    )
    
    return

        
        
if __name__ == "__main__":
    
	gdf = gpd.read_parquet(
	    f"{INTERMED_GCS}dim_stops_with_feed_service_period.parquet",
	    storage_options={"token": credentials.token}
	)
		
	export_as_csv(
		gdf, 
		export_filename = f"{PROCESSED_GCS}publish/test.csv", 
	)

	export_as_geojson(
		gdf, 
		export_filename = f"{PROCESSED_GCS}publish/test", 
	)

	
	# copy our private files to public GCS
	# make sure we can stage files ready to publish and double check first
	filepaths = [
		f"{INTERMED_GCS}dim_stops_with_feed_service_period.parquet",
		f"{PROCESSED_GCS}publish/test.csv",
		f"{PROCESSED_GCS}publish/test.geojson",
	]
	
	for f in filepaths:
        publish_utils.write_to_public_gcs(
            f,
            f"transit_ridership/{Path(f).name}",
            PUBLIC_GCS
        )
	