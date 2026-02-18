# Stop-Level Ridership Dataset (Initial Release)

This repository published sop-level ridership datasets collected from 19 California transit agencies that represent a significant share of statewide ridership.

The purpose of this release is to
- improve transparency of stop-level ridership data for public analysis and research
- standardize heterogeneous formats of agency-provided datasets
- support exploratory analysis toward a standardized stop-level ridership reporting format across agencies (such as TIDES)

## Release Content

The initial release includes two output datasets:

### Dataset 1: Metadata Dataset

A metadata table describing each agency-provided dataset collected in this round of data collection.

**File:** `metadata.csv`

**Data Description:**

| Column Name | Description |
|:------------|:------------|
| dataset_id | Unique identifier for each agency-provided dataset |
| dataset_name | Name of the initial processed (first step processing) dataset derived from the raw agency submission. |
| organization_name | Name of the transit agency that provided the dataset |
| service_name | Name of the service associated with the dataset |
| start_date_collected | Earliest date of ridership data included |
| end_date_collected | Latest date of ridership data included |
| reporting_unit | The temporal unit at which ridership values are expressed within the dataset, e.g., values reported for a day, month, year, or custom period |
| ridership_measure | Describes how ridership values should be interpreted for each reporting unit, e.g., daily values, totals or average daily values |
| geographic_grain | The spatial or operational unit represented by each record, e.g., stop, trip-stop or transaction |
| notes | Agency-reported data collection methods, known data gaps, or other contextual notes relevant to interpreting the dataset |
| gtfs_url | The URL for the GTFS dataset used for matching and obtaining stop attributes for ridership datasets with missing fields. |
| gtfs_snapshot_date | The date that the combination of organization, service and GTFS feed was present in the data warehouse. |
| gtfs_dataset_name | The GTFS dataset name that used for  used for matching and obtaining stop attributes for ridership datasets with missing fields. |
| stop_coords_from_gtfs | Indicator for whether the stop latitude and longitude in the output ridership table are from GTFS data. |
| route_id_exists | Indicator for whether the agency-provided dataset includes a route ID field |
| route_name_exists | Indicator for whether the agency-provided dataset includes a route name field |
| direction_exists | Indicator for whether the agency-provided dataset includes a direction field |
| stop_id_exists | Indicator for whether the agency-provided dataset includes a stop ID field |
| stop_name_exists | Indicator for whether the agency-provided dataset includes a stop Name field |
| stop_lat_exists | Indicator for whether the agency-provided dataset includes a stop latitude field |
| stop_lon_exists | Indicator for whether the agency-provided dataset includes a stop longitude field |
| boardings_exists | Indicator for whether the agency-provided dataset includes a boardings field |
| alightings_exists | Indicator for whether the agency-provided dataset includes an alightings field |
| ridership_exists | Indicator for whether the agency-provided dataset includes a ridership field |

---

### Dataset 2: Combined Stop-Level Ridership

A standardized dataset integrating daily stop-level ridership records across agencies.

**File:** `combined_daily_ridership.zip` (Unzip the file to get the `.csv` dataset)

**Data Description:**

| Column Name | Description |
|:------------|:------------|
| record_id | Unique identifier for each stop, service day type and reporting period combination |
| dataset_id | Identifier for the source agency-provided dataset associated with the record |
| organization_name | Name of the transit agency that provided the data |
| service_name | Name of the service associated with the dataset |
| stop_id | GTFS stop id where available |
| stop_name | Stop name (GTFS-mapped when agency didn’t provide) |
| stop_lat | Stop latitude (GTFS-mapped when agency didn’t provide or agency-provided data have more than one set of lat/lon for one stop) |
| stop_lon | Stop longitude (GTFS-mapped when agency didn’t provide or agency-provided data have more than one set of lat/lon for one stop) |
| daily_boardings | Daily boardings for the stop and reporting period. The calculation basis is documented in daily_ridership_basis column. |
| daily_alightings | Daily alightings for the stop and reporting period. The calculation basis is documented in daily_ridership_basis column. |
| daily_ridership | Daily total ridership for the stop and reporting period. The calculation basis is documented in daily_ridership_basis column. |
| day_type | Service day type associated with the ridership data (e.g., weekday, weekend, holiday, or all) |
| daily_ridership_basis | Indicates how the daily stop-level boarding/alightings/ridership value was obtained from the raw data, e.g., reported directly, reported as an average, calculated from totals, or derived from transactions |
| start_date | Start date of the ridership reporting period |
| end_date | End date of the ridership reporting period |

---

## Data Processing Overview

The combined stop-level ridership dataset was derived from heterogeneous agency-provided datasets, which vary in format, granularity and available fields. 

1. Data ingest and schema standardization. Minimal transformations necessary were applied to standardize the inputs into a consistent long-format with a shared schema and daily ridership granularity.
2. Stop attributes enrichment. This addressed missing stop attributes in agency submissions by enriching records with stop IDs, stop names, and stop coordinates sourced from GTFS data. Enrichment was applied only where these fields were absent in the agency-provided datasets. Residual gaps remain where stops could not be confidently matched.
3. Stop-level ridership production. This step aggregated ridership values for each agency, stop, day type and period. A unique key was generated for each agency-stop-day type-period combination.

## Intended Use

This release is intended for 

- exploratory analysis
- data quality assessment
- stop-level aggregation research
- supporting future statewide data collection and integration

This is an initial consolidation effort and should not be interpreted as an official statewide ridership benchmark,

## Release Version

Current version: `v1.0.0`

Datasets are available under the Github Release section:

[TODO]()