#
## Data Ingest
1. Transit agencies share files, lots of different names, number of files.
2. Local (files shared by email, etc) -> GCS (`transit_agency_raw`)
   * To facilitate upload and use same keys as the yaml, `git mv Big\ Blue\ Bus/ big_blue_bus/`...repeat throughout to rename all the folders. Handled the nested folders, made it hard to upload at once.
   * Next round, folders can match keys, no nesting, match the GCS folder structure to start.
   * Foothill is not checked in, will need to be added to yaml
4. Add Makefile

## Data Cleaning
1. Each individual transit agency's file gets put together (`Preprocess.ipynb`). Schema, number of files, how to put together all differ. --> second round might be more set schema
   * indiv transit agencies will need their data cleaned separately (ingest + clean for each agency)
   * currently saved out as xlsx -> switch to parquets in GCS (`raw`, designate suffix for `_round1`, `_round2` so all inputs from agency across multiple years can share the same folder)
   * next step joins with GTFS, and here, it'd be helpful to map the schedule name as a column
2. There is deeper cleaning on stop_ids and strings to prepare for joining with GTFS.
   * This step can be isolated conceptually, because values get overwritten to use with another data source
   * Indiv agencies combined into 1 parquet here (`intermediate`)
3. Add to Makefile
   
## Data Transformations
1. Join with GTFS data -> geoparquet
2. Post-join with GTFS, there's additional stop cleaning to fix errors.
3. One processed dataset (1 geoparquet) in `final`
4. Add to Makefile
5. Add data catalog - geoparquet should be used internally (already in bucket, cleaned, dtypes stable)
   
## Publishing Data
1. the final geoparquet can be shared in multiple formats - geoparquet / zipped geojson / zipped csv
   * figure out which file types make the most sense - try and use it and see!
2. upload to GitHub (zip)
3. upload to public GCS bucket
4. metadata files - is this needed? parquets keep the data types, unlike csvs. should keep existing markdown of column definitions of processed file.
5. Add functions to utils, add to Makefile