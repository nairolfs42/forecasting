
## Install

Python 3.12 is recommended.

macOS or Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
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

## Run the local graphical application

After activating the virtual environment and installing `requirements.txt`, run:

```bash
python main_gui.py
```

The Tkinter application can load a CSV, select period and demand columns, run
the static forecast, preview the resulting DataFrame, and optionally save the
result CSV and forecast chart. The original `main.py` command-line interface
remains available and unchanged.
