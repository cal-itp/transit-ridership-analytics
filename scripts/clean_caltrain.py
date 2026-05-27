"""
Caltrain
Unmerge first column "Month, Year of Date", and rename columns.
Add start and end date for each period.
"""
import gcsfs
import pandas as pd
from shared_vars import LOCAL_FOLDER, RAW_GCS, AGENCY_TO_GTFS_NAME_DICT, RAW_DATA_YAML

def ingest_caltrain(
    agency_name: str = "caltrain"
) -> pd.DataFrame:
    """
    """
    filename = RAW_DATA_YAML[agency_name][0]
    
    raw_caltrain = pd.read_excel(
		f"{LOCAL_FOLDER}{agency_name}/{filename}", engine="openpyxl"
	).reset_index(drop=True)
    
    raw_caltrain["Month, Year of Date"] = raw_caltrain["Month, Year of Date"].ffill()
    raw_caltrain = pd.melt(
        raw_caltrain, 
        id_vars=["Month, Year of Date", "Origin Station", "Caltrain Ridership"]
    ).rename(columns={
        "variable": "Date Type",
        "value": "Average Ridership",
        "Month, Year of Date": "Month"}
    )

    raw_caltrain["Date Type"] = raw_caltrain["Date Type"].replace({
            "Average Weekday Ridership": "Weekday",
            "Average Saturday Ridership": "Saturday",
            "Average Sunday Ridership": "Sunday",
            "Average Holiday Ridership": "Holiday"
    })

    raw_caltrain["start_date"] = pd.to_datetime(raw_caltrain["Month"], format="%B %Y")
    raw_caltrain["end_date"] = raw_caltrain["start_date"] + pd.offsets.MonthEnd(1)
    raw_caltrain["schedule_name"] = AGENCY_TO_GTFS_NAME_DICT[agency_name]

    return raw_caltrain
    

if __name__ == "__main__":
   
    agency_name = "caltrain"
    
    raw_caltrain = ingest_caltrain(agency_name)
    raw_caltrain.to_parquet(
        f"{RAW_GCS}{agency_name}/ridership_round1.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )
	
    print(f"exported: {agency_name}")