# almost makes sense for these to go first, as we'll always be visually inspecting first
# pd.read_excel() engines aren't working with GCS
clean_transit_data:
	uv run python clean_bart.py
	uv run python clean_big_blue_bus.py
	uv run python clean_caltrain.py
	uv run python clean_culver_citybus.py
	uv run python clean_fresno_area_express.py
	uv run python clean_gold_coast_transit.py
	uv run python clean_golden_gate_park_shuttle.py
	uv run python clean_golden_gate_transit.py
	uv run python clean_long_beach_transit.py
	uv run python clean_octa.py
	uv run python clean_omnitrans.py
	uv run python clean_riverside.py
	uv run python clean_sacrt.py
	uv run python clean_samtrans.py
	uv run python clean_santa_cruz_metro.py
	uv run python clean_sbmtd.py
	uv run python clean_sdmts.py
	uv run python clean_sunline.py

upload_transit_data:
	uv run python upload_raw_excel_to_gcs.py

publish_ridership_files:
	uv run python publish_to_public_gcs.py

ingest_and_upload_raw_data:
	uv run make clean_transit_data
	uv run make upload_transit_data
