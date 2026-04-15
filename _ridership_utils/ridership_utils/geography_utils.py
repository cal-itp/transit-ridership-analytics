"""
Utility functions for geospatial data.
"""
from typing import Literal

import geopandas as gpd  
import pandas as pd
import shapely  

WGS84 = "EPSG:4326"
CA_NAD83Albers_ft = "ESRI:102600"  # units are in feet
CA_NAD83Albers_m = "EPSG:3310"  # units are in meters

def create_point_geometry(
    df: pd.DataFrame,
    longitude_col: str = "stop_lon",
    latitude_col: str = "stop_lat",
    crs: str = WGS84,
) -> gpd.GeoDataFrame:
    """
    Parameters:
    df: pandas.DataFrame to turn into geopandas.GeoDataFrame,
        default dataframe in mind is gtfs_schedule.stops

    longitude_col: str, column name corresponding to longitude
                    in gtfs_schedule.stops, this column is "stop_lon"

    latitude_col: str, column name corresponding to latitude
                    in gtfs_schedule.stops, this column is "stop_lat"

    crs: str, coordinate reference system for point geometry
    """
    # Default CRS for stop_lon, stop_lat is WGS84
    df = df.assign(
        geometry=gpd.points_from_xy(df[longitude_col], df[latitude_col], crs=WGS84)
    )

    # ALlow projection to different CRS
    gdf = gpd.GeoDataFrame(df).to_crs(crs)

    return gdf


def make_linestring(x: str) -> shapely.geometry.LineString:
    """
    Convert WKT string into a linestring.
    
    Laurie's example: 
    https://github.com/cal-itp/data-analyses/blob/752eb5639771cb2cd5f072f70a06effd232f5f22/gtfs_shapes_geo_examples/example_shapes_geo_handling.ipynb
    """
    # shapely errors if the array contains only one point
    if len(x) > 1:
        # each point in the array is wkt
        # so convert them to shapely points via list comprehension
        as_wkt = [shapely.wkt.loads(i) for i in x]
        
        return shapely.geometry.LineString(as_wkt)

        
def convert_to_gdf(
    df: pd.DataFrame, 
    geom_col: str,
    geom_type: Literal["point", "line"]
) -> gpd.GeoDataFrame:
    """
    For stops, we want to make pt_geom a point.
    For vp_path and shapes, we want to make pt_array a linestring.
    """
    if geom_type == "point":
        df["geometry"] = [shapely.wkt.loads(x) for x in df[geom_col]]

    elif geom_type == "line":
        df["geometry"] = df[geom_col].apply(make_linestring)

    gdf = gpd.GeoDataFrame(
        df.drop(columns = geom_col), geometry="geometry", 
        crs=WGS84
    )

    return gdf