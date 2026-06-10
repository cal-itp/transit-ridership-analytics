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
   * TODOs for 2nd round, possibly for 1st: 
      - `snakecase` all columns for 2nd round, this would change the subsequent ways columns are called
      - dtypes need to be set with `.astype()` early on, esp because parquets will store it. some look mixed, int or string `routes can be 1, 2, 3, but also 1A, so it's string`. metadata yaml no longer needed if parquets bring dtypes correctly. 
      - column names set early on, similar schema across all operators. if snakecased, then renaming happens only once, rather than throughout scripts. dtype would have to work across all operators (cannot be integer if there is 1+ operator with a string). might end up being the same as GTFS dtypes.
   * next step joins with GTFS, and here, it'd be helpful to map the schedule name as a column
2. There is deeper cleaning on stop_ids and strings to prepare for joining with GTFS.
   * This step can be isolated conceptually, because values get overwritten to use with another data source
   * Transit agency's stop lat/lon sometimes is provided. There is deduping and keeping max. Should it matter, if we're bringing in GTFS? 
   * Indiv agencies combined into 1 parquet here (`intermediate`)
3. Add to Makefile
   
## Data Transformations
1. Join with GTFS data -> geoparquet
2. Post-join with GTFS, there's additional stop cleaning to fix errors.
   * one gap is sampling warehouse dates. move to bringing in all active feeds, universe of stops that could join with ridership.
   * how will stops be deduplicated? once we bring in universe of stops, we have different issue of having fanout.
   * one cleaning step now is that stops should show same information, regardless of whether the versioned stop shows differences (stop_names differ slightly). this will also need to be considered with the deduplicating, though it's more akin to labeling.
   * the join should support the final labeling with as few steps as possible
3. One processed dataset (1 geoparquet) in `final`
4. Add to Makefile
5. Add data catalog - geoparquet should be used internally (already in bucket, cleaned, dtypes stable)
   
## Publishing Data
1. the final geoparquet can be shared in multiple formats - geoparquet / geojson / csv
2. write this to private GCS first. allow changes to be made and checked before overwriting public files.
3. copy private GCS files over to public GCS bucket
4. metadata files - is this needed? parquets keep the data types, unlike csvs. should keep existing markdown of column definitions of processed file.
   * might need to also shared metadata parquet file (contents of `agency_config.yml`)
5. Add functions to utils, add to Makefile