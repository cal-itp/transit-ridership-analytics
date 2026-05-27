"""
SacRT

1. Join ridership and stops table
2. Differentiate weekday and weekend ridership
Note: For the routes that run on weekends, weekends are included in the agg counts. 
For the routes that don't run on weekends, only weekdays are included in agg conuts. 
See the indicator columns from Monday to Sunday.

snakecase could be a way to clean columns for all transit agencies, adjust rest of scripts too
"""
import gcsfs
import pandas as pd

from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_sacrt_ridership(
    agency_name: str = "sacrt",
    filename: str = "ridership.txt.csv"
) -> pd.DataFrame:
    """
    """    
    raw_sacrt_ridership = pd.read_csv(
        f"{LOCAL_FOLDER}{agency_name}/{filename}", 
	)
    raw_sacrt_ridership.columns = raw_sacrt_ridership.columns.str.lower()

    # cast indicator cols to int
    dow_cols = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    raw_sacrt_ridership[dow_cols] = raw_sacrt_ridership[dow_cols].apply(pd.to_numeric, errors="coerce").astype("Int64")
    
    raw_sacrt_ridership = raw_sacrt_ridership.loc[:, ~raw_sacrt_ridership.columns.str.contains("^unnamed", case=False)]
    
    raw_sacrt_ridership_grouped = raw_sacrt_ridership.groupby(
        ["ridership_start_date", "ridership_end_date", "service_start_time", "service_end_time",
         "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "route_id",
         "direction_id", "stop_id"], dropna=False
    )[["average_boardings", "average_alightings"]].sum().reset_index()   

    raw_sacrt_ridership_grouped = raw_sacrt_ridership_grouped.assign(
        start_date = pd.to_datetime(raw_sacrt_ridership_grouped["ridership_start_date"], 
                                    format="%Y%m%d").dt.strftime("%Y-%m-%d"),
		end_date = pd.to_datetime(raw_sacrt_ridership_grouped["ridership_end_date"], 
                                  format="%Y%m%d").dt.strftime("%Y-%m-%d")
	)
    
    return raw_sacrt_ridership_grouped

    
def ingest_sacrt_stops(
    agency_name: str = "sacrt",
    filename: str = "stops.txt.csv"
):

    raw_sacrt_stops = pd.read_csv(f"{LOCAL_FOLDER}{agency_name}/{filename}")
    raw_sacrt_stops = raw_sacrt_stops.dropna(how="all")
    raw_sacrt_stops['stop_id'] = raw_sacrt_stops['stop_id'].astype("int64")
    raw_sacrt_stops['stop_code'] = raw_sacrt_stops['stop_code'].astype("int64")
    raw_sacrt_stops = raw_sacrt_stops.loc[:, ~raw_sacrt_stops.columns.str.contains("^unnamed", case=False)]

    return raw_sacrt_stops


def ingest_sacrt_routes(
    agency_name: str = "sacrt",
    filename: str = "routes.txt.csv"
):
	raw_sacrt_routes = pd.read_csv(f"{LOCAL_FOLDER}{agency_name}/{filename}")
	raw_sacrt_routes = raw_sacrt_routes.dropna(how="all")
	raw_sacrt_routes['route_type'] = raw_sacrt_routes['route_type'].astype("int64")
	
	return raw_sacrt_routes

    
def merge_ridership_with_stop_and_routes(
	ridership_df: pd.DataFrame,
	stop_df: pd.DataFrame,
	routes_df: pd.DataFrame
) -> pd.DataFrame:
	
	raw_sacrt_export = pd.merge(
		ridership_df, 
		stop_df, 
		how="left", 
		on="stop_id"
	).merge(
		routes_df, 
		how="left", 
		on="route_id"
	)
	
	raw_sacrt_export = raw_sacrt_export.assign(
		start_date = pd.to_datetime(raw_sacrt_export.start_date),
		end_date = pd.to_datetime(raw_sacrt_export.end_date),
		day_type = raw_sacrt_export.apply(
			lambda x: 
			"weekday" if x.saturday == 0 and x.sunday == 0
			else "all", axis=1,
		),
		schedule_name = AGENCY_TO_GTFS_NAME_DICT[agency_name]
	)

	return raw_sacrt_export
	
if __name__ == "__main__":
   
    agency_name = "sacrt"

	# define which files match ridership, stops, routes
    ridership = ingest_sacrt_ridership(agency_name, filename = RAW_DATA_YAML[agency_name][0])
    stops = ingest_sacrt_stops(agency_name, filename = RAW_DATA_YAML[agency_name][2])
    routes = ingest_sacrt_routes(agency_name, filename = RAW_DATA_YAML[agency_name][1])

    raw_sacrt_export = merge_ridership_with_stop_and_routes(ridership, stops, routes)

	# only export 1 file, no longer by bus/light_rail
    raw_sacrt_export.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print(f"exported: {agency_name}")