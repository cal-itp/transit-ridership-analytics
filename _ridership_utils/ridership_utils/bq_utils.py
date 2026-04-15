"""
pandas_gbq utils to download Big Query tables
"""
from typing import Literal

import geopandas as gpd
import google.auth
import pandas as pd
import pandas_gbq
from gtfs_curator_shared_utils import geography_utils

credentials, project = google.auth.default()


def basic_sql_query(
    project_name: str, 
    dataset_name: str, 
    table_name: str, 
    columns: list = None
) -> str:
    """
    Set up the basic sql query needed, which is the entire table.
    """
    if isinstance(columns, list):
        subset_columns_as_string = list_as_string(list(columns))
        sql_query = f"SELECT {subset_columns_as_string} FROM `{project_name}`.`{dataset_name}`.`{table_name}`"
        
    else:
        sql_query = f"SELECT * FROM  `{project_name}`.`{dataset_name}`.`{table_name}`"        
    
    return sql_query


def list_as_string(list_of_columns: list) -> str:
    """
    Unpack a list of columns as a string, to use in sql select statement.
    """
    columns_written_out = ", ".join(list_of_columns)
    return columns_written_out


def add_sql_date_filter(date_col: str, start_date: str, end_date: str) -> str:
    """
    Add a where condition to filter by date, coerce the dates so sql_query is read correctly.
    """
    where_condition = f"{date_col} >= DATE('{start_date}') AND {date_col} <= DATE('{end_date}')"

    return where_condition


def download_table(
    project_name: str = "cal-itp-data-infra",
    dataset_name: str = "mart_gtfs",
    table_name: str = "",
    date_col: Literal["service_date", "month_first_day", None] = "",
    start_date: str = "",
    end_date: str = "",
    columns: list = None,
    geom_col: str = None,
    geom_type: Literal["point", "line"] = None,
) -> Literal[pd.DataFrame, gpd.GeoDataFrame]:
    """
    Set up a basic query and use pandas_gbq to import.
    Coerce datetime column and convert to gdf if needed.
    """
    basic_query = basic_sql_query(project_name, dataset_name, table_name)
    where_condition = add_sql_date_filter(date_col, start_date, end_date)
    sql_query_statement = f"{basic_query} WHERE {where_condition}"

    if date_col is None:
        df = pandas_gbq.read_gbq(basic_query, project_id=project_name, dialect="standard", credentials=credentials)

        print(f"query: {basic_query}")

    if date_col is not None:
        df = pandas_gbq.read_gbq(
            sql_query_statement, project_id=project_name, dialect="standard", credentials=credentials
        ).astype({date_col: "datetime64[ns]"})

        print(f"query: {sql_query_statement}")

    if geom_col is not None:

        df = geo_utils.convert_to_gdf(df, geom_col, geom_type)

    return df


def download_table_custom_filter(
    project_name: str = "cal-itp-data-infra",
    dataset_name: str = "mart_gtfs",
    table_name: str = "",
    date_col: Literal["service_date", "month_first_day", None] = "",
    start_date: str = "",
    end_date: str = "",
    columns: list = None,
    geom_col: str = None,
    geom_type: Literal["point", "line"] = None,
    custom_filter_statement: str = ""
) -> Literal[pd.DataFrame, gpd.GeoDataFrame]:
    """
    Set up a basic query and use pandas_gbq to import.
    Coerce datetime column and convert to gdf if needed.
    """
    basic_query = basic_sql_query(project_name, dataset_name, table_name, columns)
    date_condition = add_sql_date_filter(date_col, start_date, end_date)
    
    if date_col is None:
        sql_query_statement = f"{basic_query} WHERE {custom_filter_statement}"
    if custom_filter_statement != "":
        sql_query_statement = f"{basic_query} WHERE {date_condition} AND {custom_filter_statement}"

    df = pandas_gbq.read_gbq(
        sql_query_statement, project_id=project_name, dialect="standard", credentials=credentials
    ).astype({date_col: "datetime64[ns]"})

    print(f"query: {sql_query_statement}")

    if geom_col is not None:

        df = geography_utils.convert_to_gdf(df, geom_col, geom_type)

    return df