import gcsfs
import pandas as pd

from ridership_utils import utils, geography_utils

GCS_FILE_PATH = "gs://calitp-analytics-data/data-analyses/transit-ridership-analytics/"
AGENCY_GCS = f"{GCS_FILE_PATH}/transit_agency_raw/"
RAW_GCS = f"{GCS_FILE_PATH}raw/"

transit_agencies_files = {
	"bart",
	"big_blue_bus",
	"caltrain": "one_file.xlsx",
	"culver_city": ["Ridership by Trip_7_14_25-8_26_25.csv", "Ridership by Time Period, Route, and Stop_7_14_25-8_25_25.csv"]
}


def import_culver_city(abbrev_name: str = "culver_city") -> pd.DataFrame:
	files = [
		"Ridership by Trip_7_14_25-8_26_25.csv", 
		"Ridership by Time Period, Route, and Stop_7_14_25-8_25_25.csv"
	]

	df = pd.read_csv(
		f"{AGENCY_GCS}/{abbrev_name}/Ridership by Trip_7_14_25-8_26_25.csv"
	)
	df2 = utils.to_snakecase(df)
	# other stuff, renaming columns, fixing dtypes

	df2.to_parquet(
		f"{RAW_GCS}{abbrev_name}_by_stop.parquet", filesystem=gcsfs.GCSFileSystem()	
	)
	
	return

def import_excel_export_parquet(filename: str):
	df = pd.read_excel(filename)
	df.to_parquet(
		f"{GCS_FILE_PATH}{filename}.parquet"
	)
	return

def import_excel_export_geoparquet(filename: str):
	df = pd.read_excel(filename)

	gdf = geography_utils.create_point_geometry(
		df,
		longitude_col = "x",
	    latitude_col = "y"
	)

	utils.geoparquet_gcs_export(
		gdf,
		GCS_FILE_PATH,
		filename
	)

	return