"""
pandas_gbq utils to download Big Query tables
"""

from typing import Literal

import geopandas as gpd
import google.auth
import pandas as pd
import pandas_gbq
from google.cloud import bigquery
from ridership_utils import geography_utils

credentials, project = google.auth.default()


def basic_sql_query(project_name: str, dataset_name: str, table_name: str, columns: list = None) -> str:
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
    if start_date == "" and end_date == "":
        where_condition = ""
    else:
        where_condition = f"{date_col} >= DATE('{start_date}') AND {date_col} <= DATE('{end_date}')"

    return where_condition


def exclude_interval_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    BigQuery has interval columns.
    Drop these, because these will error when saving out parquets.
    """
    interval_cols = [c for c in df.columns if "_interval" in c]

    return df.drop(columns=interval_cols)


def fix_date_columns(
    df: pd.DataFrame,
    # allowed_date_cols: list = ["service_date", "date", "month_first_day"]
) -> pd.DataFrame:
    """
    dbdate shows up when it's BigQuery DATE type.
    For columns we do use, set these as datetime.

    """
    date_cols = df.select_dtypes("dbdate").columns.tolist()

    df[date_cols] = df[date_cols].astype("datetime64[ns]")

    return df


def timezone_aware_datetime_columns(df, datetime_cols: list):
    """
    Timezone-aware columns need to be handled.

    # these are timezone-aware, so should we localize to America/Los_Angeles or keep as UTC?
    ["location_timestamp", "header_timestamp", "vehicle_timestamp"]
    """
    return


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
    date_condition = add_sql_date_filter(date_col, start_date, end_date)

    if date_col is None:
        sql_query_statement = basic_query
    if (date_col is not None) and (date_condition != ""):
        sql_query_statement = f"{basic_query} WHERE {date_condition}"

    df = pandas_gbq.read_gbq(sql_query_statement, project_id=project_name, dialect="standard", credentials=credentials)

    print(f"query: {sql_query_statement}")

    if geom_col is not None:

        df = geography_utils.convert_to_gdf(df, geom_col, geom_type)

    df = df.pipe(fix_date_columns).pipe(exclude_interval_columns)

    return df


def bq_faster_download(sql_query: str, **kwargs) -> pd.DataFrame:
    """
    This function will take a sql_query string,
    as well as support parameterized queries.
    parameterized queries use a job_config kwarg.
    Use set_bq_query_params() to set this up.

    docs.cloud.google.com/bigquery/docs/parameterized-queries
    """
    if "project" in kwargs:
        project = kwargs.pop("project")
    if "credentials" in kwargs:
        credentials = kwargs.pop("credentials")

    client = bigquery.Client(project=project, credentials=credentials)

    query_job = client.query(sql_query, **kwargs)

    df = query_job.result().to_dataframe()

    df = df.pipe(fix_date_columns).pipe(exclude_interval_columns)

    return df


def set_bq_query_params(
    scalar_query_parameter: dict = None,
    array_query_parameter: dict = None,
):
    """
    Example:
    scalar_query_parameter = {"gender": "M"}
    array_query_parameter = {"states": ["WA", "WI", "WV", "WY"]}


    Use this function to populate the query_parameters argument.
    By default, it's an empty list.

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("gender", "STRING", "M"),
            bigquery.ArrayQueryParameter("states", "STRING", ["WA", "WI", "WV", "WY"]),
        ]
    )
    """
    query_params = []

    if scalar_query_parameter is not None:
        for column_name, column_value in scalar_query_parameter.items():
            if isinstance(column_value, str):
                one_param = bigquery.ScalarQueryParameter(column_name, "STRING", column_value)

            elif isinstance(column_value, int):
                one_param = bigquery.ScalarQueryParameter(column_name, "INT64", column_value)

            query_params.append(one_param)

    if array_query_parameter is not None:
        for column_name, column_list_of_values in array_query_parameter.items():
            first_value = column_list_of_values[0]
            if isinstance(first_value, str):
                one_param = bigquery.ArrayQueryParameter(column_name, "STRING", column_list_of_values)

            elif isinstance(first_value, int):
                one_param = bigquery.ArrayQueryParameter(column_name, "INT64", column_list_of_values)

            query_params.append(one_param)

    return query_params
