GCS_FILE_PATH = "gs://calitp-analytics-data/data-analyses/transit-ridership-analytics/"
AGENCY_GCS = f"{GCS_FILE_PATH}transit_agency_raw/"
RAW_GCS = f"{GCS_FILE_PATH}raw/"
INTERMED_GCS = f"{GCS_FILE_PATH}intermediate/"
PROCESSED_GCS = f"{GCS_FILE_PATH}processed/"

# Map the existing agency names "City of Fresno", "BART" to the schedule_name that is used in warehouse
# GTFS stop data comes in feeds, which use schedule_name
AGENCY_TO_GTFS_NAMES_DICT = {
	
}