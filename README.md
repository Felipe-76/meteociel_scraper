# Meteociel Scraper

A Python package for scraping historical and forecast meteorological data from [Meteociel.fr](https://www.meteociel.fr/). It allows you to programmatically download, process, and export weather data for a given station and date range, or retrieve weather forecasts from various Meteociel models.

## Features
- **Historical Data**: Download hourly meteorological observations for a single date or a range of dates for a given station.
- **Forecast Data**: Retrieve weather forecasts (previsions) for a given location and model (e.g., ARPEGE, AROME, WRF, ICON).
- **CSV Export**: Optionally export all results to CSV files for further analysis.

## Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd meteociel_scraper
   ```
2. Install dependencies (preferably in a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

See `example.ipynb` for detailed, runnable examples.

### 1. Historical Data for a Single Date
```python
from get_meteo.get_meteo_data import get_meteociel_data

date = "2023-01-01"
meteostation = "7157"
df, csv_path = get_meteociel_data(
    date=date,
    meteostation=meteostation,
    csv_export=True,  # Set to True to export as CSV
)
```

### 2. Historical Data for a Date Range
```python
from get_meteo.get_meteo_data import get_historic_meteociel

start_date = "2023-01-01"
end_date = "2023-01-03"
station = "7157"
df, csv_path = get_historic_meteociel(
    start_date=start_date,
    end_date=end_date,
    meteostation=station,
    csv_export=True,
)
```

### 3. Weather Forecasts (Previsions)
```python
from get_meteo.get_prevision_data import get_prevision_data

code = "32104"  # Meteociel location code
prevision = "previsions-arpege-1h"  # Model type (see below)
df_prev, path_prev = get_prevision_data(
    code=code,
    prevision=prevision,
    csv_export=True,
)
```
- **Supported models for `prevision`:**
  - "previsions"
  - "previsions-wrf"
  - "previsions-wrf-1h"
  - "previsions-arome"
  - "previsions-arome-1h"
  - "previsions-arpege-1h"
  - "previsions-iconeu"
  - "previsions-icond2"

To find the `code` for your location, visit a forecast page on Meteociel and look for the number in the URL (or use the search box on the site).

## Output
- CSV files are saved in subfolders of `files/meteo_tables/` (e.g., `meteociel_scraping/`, `meteo_prev/`).
- If these folders do not exist, they will be created automatically by the script.

## Notes
- All times are handled in the specified timezone (default: Europe/Paris) and converted to UTC in the output, for the historic scraping two more dates are added at the start and at the end of the range to include the necessary datapoints for any selected Timezone.
- Some columns may be missing or have NaN values if data is unavailable for a given hour.
- The package relies on the structure of Meteociel.fr; if the site changes, scraping may break.
- For advanced usage, see the docstrings in `get_meteo/get_meteo_data.py` and `get_meteo/get_prevision_data.py`.

## Requirements
See `requirements.txt` for all dependencies (notably: `requests`, `beautifulsoup4`, `pandas`, `numpy`).
