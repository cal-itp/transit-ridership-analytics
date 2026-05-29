"""
Script to upload raw Excel or csv files
from each individual transit agency.
"""
import gcsfs
import yaml

from pathlib import Path
from shared_vars import AGENCY_GCS, LOCAL_FOLDER, RAW_DATA_YAML

fs = gcsfs.GCSFileSystem()

def upload_files_from_local_to_gcs(raw_data_dict: dict):
    for one_operator_name in list(raw_data_dict.keys()):
        
        print(f"start {one_operator_name}")

        operator_file_list = raw_data_dict[one_operator_name]
		
        for one_file in operator_file_list:

            local_file = Path(LOCAL_FOLDER).joinpath(one_operator_name, one_file).resolve()
            gcs_file = f"{AGENCY_GCS}{one_operator_name}/{one_file}"
            #print(f"{local_file} is uploaded as {gcs_file}")
            fs.put_file(local_file, gcs_file) 

        print(f"uploaded {one_operator_name}")

    return

def download_files_from_gcs(raw_data_dict: dict):
    for one_operator_name in list(raw_data_dict.keys()):
        print(f"start {one_operator_name}")

        operator_file_list = raw_data_dict[one_operator_name]
		
        for one_file in operator_file_list:

            local_file = Path(LOCAL_FOLDER).joinpath(one_operator_name, one_file).resolve()
            gcs_file = f"{AGENCY_GCS}{one_operator_name}/{one_file}"
            fs.get_file(gcs_file, local_file) 
        
        print(f"downloaded {one_operator_name}")

    return
 

if __name__ == "__main__":

	# datasets collected in round 1

	# Loop through each operator and upload the file into its own folder
	#upload_files_from_local_to_gcs(RAW_DATA_YAML)
    download_files_from_gcs(RAW_DATA_YAML)
		