# almost makes sense for these to go first, as we'll always be visually inspecting first
# pd.read_excel() engines aren't working with GCS
clean_transit_data:
	python clean_bart.py
	python clean_big_blue_bus.py
	python clean_caltrain.py
	python clean_culver_citybus.py
	python clean_fresno_area_express.py
	python clean_gold_coast_transit.py
	python clean_golden_gate_park_shuttle.py
	python clean_golden_gate_transit.py
	python clean_long_beach_transit.py
	python clean_octa.py
	python clean_omnitrans.py
	# python clean_riverside.py # two part, upload transactions, save as parquet, then aggregate to stop
	python clean_sacrt.py
	python clean_samtrans.py
	python clean_santa_cruz_metro.py
	python clean_sbmtd.py
	python clean_sdmts.py
	python clean_sunline.py

upload_transit_data:
	python upload_raw_excel_to_gcs.py

publish_ridership_files:
	python publish_to_public_gcs.py

ingest_and_upload_raw_data:
	make clean_transit_data
	make upload_transit_data	