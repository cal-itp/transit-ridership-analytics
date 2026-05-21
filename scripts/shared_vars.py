import yaml
from pathlib import Path

GCS_FILE_PATH = "gs://calitp-analytics-data/data-analyses/transit-ridership-analytics/"
AGENCY_GCS = f"{GCS_FILE_PATH}transit_agency_raw/"
RAW_GCS = f"{GCS_FILE_PATH}raw/"
INTERMED_GCS = f"{GCS_FILE_PATH}intermediate/"
PROCESSED_GCS = f"{GCS_FILE_PATH}processed/"

RAW_DATA_YAML_PATH = Path("raw_datasets.yml")

with open(RAW_DATA_YAML_PATH) as f:
    RAW_DATA_YAML = yaml.safe_load(Path(RAW_DATA_YAML_PATH).read_text())

# Map the existing agency names "City of Fresno", "BART" to the schedule_name that is used in warehouse
# GTFS stop data comes in feeds, which use schedule_name
AGENCY_TO_GTFS_NAME_DICT = {
    "bart": "Bay Area 511 BART Schedule",
    "big_blue_bus": "Big Blue Bus Schedule",
    "caltrain": "Bay Area 511 Caltrain Schedule",
	"fresno_area_express": "Fresno Schedule", # or is it Fresno County Schedule
	"culver_citybus": "Culver City Schedule",
	"foothill_transit": "Foothill Schedule",
	"gold_coast_transit": "Gold Coast Schedule",
	"golden_gate_park_shuttle": "Bay Area 511 Golden Gate Park Shuttle Schedule",
	"golden_gate_transit": "Bay Area 511 Golden Gate Transit Schedule",
	"long_beach_transit": "Long Beach Schedule",
	"octa": "OCTA Schedule",
	"omnitrans": "OmniTrans Schedule",
	"sbmtd": "SBMTD Schedule",
	"sdmts": "San Diego Schedule",
	"sacrt": "Sacramento Schedule",
	"samtrans": "Bay Area 511 SamTrans Schedule",
	"santa_cruz_metro": "Santa Cruz Schedule",
	"sunline_transit": "SunLine Avail Schedule",
     # while mapping names, should all columns become snakecase?   
}

