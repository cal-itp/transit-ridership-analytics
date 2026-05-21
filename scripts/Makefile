# almost makes sense for these to go first, as we'll always be visually inspecting first
# pd.read_excel() engines aren't working with GCS
clean_transit_data:
	python clean_bart.py
	python clean_big_blue_bus.py

upload_transit_data:
	python upload_raw_excel_to_gcs.py

ingest_and_upload_raw_data:
	make clean_transit_data
	make upload_transit_data	