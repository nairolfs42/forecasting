
## Install

Python 3.12 is recommended.

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```
or
```single script
source ./setup.sh
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
note : can also try
``` additional powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the local graphical application
```bash
python main_gui.py
```

The Tkinter application can load a CSV, select a demand column, run the static
forecast, preview the resulting DataFrame, and optionally save the result CSV
and forecast chart. By default, CSV row order is treated as chronological order
and periods `1..n` are generated automatically. A real period or date column can
still be selected for unsorted data or meaningful output labels. 


## CLI usage

## Inspect a CSV

Running without column selections prints a profile of the available columns:

```bash
python main.py test_data/test_data_1.csv
```

## Run a sample quarterly static forecast

```bash
python main.py test_data/test_data_1.csv \
  --period-column period_t \
  --demand-column demand_dt \
  --output output/static_forecast.csv \
  --plot output/static_forecast.png
```



