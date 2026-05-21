"""
Script to upload raw Excel or csv files
from each individual transit agency.
"""
import gcsfs
import yaml

from pathlib import Path
from shared_vars import AGENCY_GCS

fs = gcsfs.GCSFileSystem()

if __name__ == "__main__":

	# datasets collected in round 1
	RAW_DATA_YAML = Path("raw_datasets.yml")

	with open(RAW_DATA_YAML) as f:
		# .read_text() needs to read a path
		# otherwise it returns the string "raw_datasets.yml"
	    raw_data_dict = yaml.safe_load(RAW_DATA_YAML.read_text())


	# This is where the datasets are uploaded locally 
	# Switch for round 2 (this folder will not exist in GitHub after round 1)
	LOCAL_FOLDER = Path("../transit_agency_ridership_raw_datasets/")

	# Loop through each operator and upload the file into its own folder
	for one_operator_name in list(raw_data_dict.keys()):
		
		operator_file_list = raw_data_dict[one_operator_name]
		
		print(f"start {one_operator_name}")
		
		for one_file in operator_file_list:
			
			# can print what these paths look like in dry run
			local_file = LOCAL_FOLDER.joinpath(one_operator_name, one_file).resolve()
			gcs_file = f"{AGENCY_GCS}{one_operator_name}/{one_file}"
			#print(f"{local_file} is uploaded as {gcs_file}")
			
			fs.put(local_file, gcs_file)
			
		print(f"uploaded {one_operator_name}")
		
		