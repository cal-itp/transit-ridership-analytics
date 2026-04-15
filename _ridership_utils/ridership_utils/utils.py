"""
General utility functions.
"""
import base64
import geopandas as gpd
import gcsfs
import os
import pandas as pd
import shutil
from pathlib import Path
from typing import Literal, Optional, Union

fs = gcsfs.GCSFileSystem()

CALITP_BQ_MAX_BYTES = os.environ.get("CALITP_BQ_MAX_BYTES", 5_000_000_000)
CALITP_BQ_LOCATION = os.environ.get("CALITP_BQ_LOCATION", "us-west2")

def to_snakecase(df: pd.DataFrame):
    """
    Convert DataFrame column names to snakecase.

    Note that this function also strips some non-ascii charactures, such as '"'.
    """

    return df.rename(
        columns=lambda s: s.lower()
        .replace(" ", "_")
        .replace("&", "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace(".", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace('"', "")
        .replace("'", "")
    ).rename(columns=lambda s: "_%s" % s if s[0].isdigit() else s)


def sanitize_file_path(file_name: str) -> str:
    """
    Remove the .parquet or .geojson in a filepath.
    """
    return str(Path(file_name).stem)


def parse_file_directory(file_name: str) -> str:
    """
    Grab the directory of the filename.
    For GCS bucket, we do not want '.' as the parent
    directory, we want to parse and put together the
    GCS filepath correctly.
    """
    if str(Path(file_name).parent) != ".":
        return str(Path(file_name).parent)
    else:
        return ""


def geoparquet_gcs_export(
    gdf: gpd.GeoDataFrame,
    gcs_file_path: str,
    file_name: str,
    **kwargs,
):
    """
    Save geodataframe as parquet locally,
    then move to GCS bucket and delete local file.

    gdf: geopandas.GeoDataFrame
    gcs_file_path: str
                    Ex: gs://calitp-analytics-data/data-analyses/my-folder/
    file_name: str
                Filename, with or without .parquet.
    """
    # Parse out file_name into stem (file_name_sanitized)
    # and parent (file_directory_sanitized)
    file_name_sanitized = Path(sanitize_file_path(file_name))
    file_directory_sanitized = parse_file_directory(file_name)

    # Make sure GCS path includes the directory we want the file to go to
    expanded_gcs = f"{Path(gcs_file_path).joinpath(file_directory_sanitized)}/"
    expanded_gcs = str(expanded_gcs).replace("gs:/", "gs://")

    gdf.to_parquet(f"{file_name_sanitized}.parquet", **kwargs)
    fs.put(
        f"{file_name_sanitized}.parquet",
        f"{str(expanded_gcs)}{file_name_sanitized}.parquet",
    )
    os.remove(f"{file_name_sanitized}.parquet", **kwargs)


def geojson_gcs_export(
    gdf: gpd.GeoDataFrame,
    gcs_file_path: str,
    file_name: str,
    geojson_type: str = "geojson",
):
    """
    Save geodataframe as geojson locally,
    then move to GCS bucket and delete local file.

    gcs_file_path: str
        Ex: gs://calitp-analytics-data/data-analyses/my-folder/
    file_name: str
        name of file (with .geojson or .geojsonl).
    """

    if geojson_type == "geojson":
        DRIVER = "GeoJSON"
    elif geojson_type == "geojsonl":
        DRIVER = "GeoJSONSeq"
    else:
        raise ValueError("Not a valid geojson type! Use `geojson` or `geojsonl`")

    file_name_sanitized = sanitize_file_path(file_name)

    gdf.to_file(f"./{file_name_sanitized}.{geojson_type}", driver=DRIVER)

    fs.put(
        f"./{file_name_sanitized}.{geojson_type}",
        f"{gcs_file_path}{file_name_sanitized}.{geojson_type}",
    )
    os.remove(f"./{file_name_sanitized}.{geojson_type}")


def read_geojson(
    gcs_file_path: str,
    file_name: str,
    geojson_type: Literal["geojson", "geojsonl"] = "geojson",
    save_locally: bool = False,
) -> gpd.GeoDataFrame:
    """
    Parameters:
    gcs_file_path: str
        Ex: gs://calitp-analytics-data/data-analyses/my-folder/
    file_name: str
        name of file (with or without the .geojson).
    geojson_type: str.
        valid values are geojson or geojsonl.
    save_locally: bool
        defaults to False. if True, will save geojson locally.
    """
    file_name_sanitized = sanitize_file_path(file_name)

    object_path = fs.open(f"{gcs_file_path}{file_name_sanitized}.{geojson_type}")
    gdf = gpd.read_file(object_path)

    if geojson_type == "geojson":
        DRIVER = "GeoJSON"
    elif geojson_type == "geojsonl":
        DRIVER = "GeoJSONSeq"

    if save_locally:
        gdf.to_file(f"./{file_name}.{geojson_type}", driver=DRIVER)

    return gdf


def make_shapefile(gdf: gpd.GeoDataFrame, path: Union[Path, str]) -> tuple[Path, Path]:
    """
    Make a zipped shapefile and save locally
    Parameters
    ==========
    gdf: gpd.GeoDataFrame to be saved as zipped shapefile
    path: str, local path to where the zipped shapefile is saved.
            Ex: "folder_name/census_tracts"
                "folder_name/census_tracts.zip"

    Remember: ESRI only takes 10 character column names!!

    Returns a folder name (dirname) where the shapefile is stored and
    a filename. Both are strings.
    """
    if isinstance(path, str):
        path = Path(path)

    # Use pathlib instead of os
    # https://towardsdatascience.com/goodbye-os-path-15-pathlib-tricks-to-quickly-master-the-file-system-in-python-881213ca7c21
    # Grab first element of path (can input filename.zip or filename)
    dirname = path.parent.joinpath(path.stem)
    print(f"Path name: {path}")
    print(f"Dirname (1st element of path): {dirname}")

    # Make sure there's no folder with the same name
    shutil.rmtree(dirname, ignore_errors=True)

    # Make folder
    Path.mkdir(dirname, parents=True)
    shapefile_name = Path(path.stem).with_suffix(".shp")
    print(f"Shapefile name: {shapefile_name}")

    # Export shapefile into its own folder with the same name
    gdf.to_file(driver="ESRI Shapefile", filename=dirname.joinpath(shapefile_name))
    print(f"Shapefile component parts folder: {dirname}/{shapefile_name}")

    return dirname, shapefile_name


def make_zipped_shapefile(
    gdf: gpd.GeoDataFrame,
    local_path: Union[str, Path],
    gcs_folder: Optional[str] = None,
):
    """
    Make a zipped shapefile and save locally
    Parameters
    ==========
    gdf: gpd.GeoDataFrame to be saved as zipped shapefile
    local_path: str, local path to where the zipped shapefile is saved.
            Ex: "folder_name/census_tracts"
                "folder_name/census_tracts.zip"
    gcs_folder: str, the gcs folder to save the local_path file name into.
                Ex: if local_path is "folder_name/census_tracts.zip" abd
                gcs_folder is "gs://my_bucket/new_folder",
                the object in GCS would be "gs//my_bucket/new_folder/census_tracts.zip"

    Remember: ESRI only takes 10 character column names!!
    """
    dirname, shapefile_name = make_shapefile(gdf, local_path)

    # Zip it up
    shutil.make_archive(dirname.name, "zip", dirname)
    # Remove the unzipped folder
    shutil.rmtree(dirname.name, ignore_errors=True)

    if gcs_folder:
        if gcs_folder[-1] != "/":
            gcs_folder = f"{gcs_folder}/"

        fs.put(
            f"./{dirname.parent}.zip",
            f"{gcs_folder}{dirname.parent}.zip",
        )