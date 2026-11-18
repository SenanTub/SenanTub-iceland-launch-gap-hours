# What one Iceland launch buys

Does a weather balloon launched from Iceland spend more time over the thinly observed North Atlantic and Arctic than one launched from the northeastern US? I built a simple flight model with real winds to find out.

**Short answer: no, except over the Arctic.** Per launch, an Iceland balloon logs fewer hours in the observing gap than a Cambridge or New York balloon, drifting or steered. Its one edge is the Arctic part of the gap, at about 1.2 to 1.5 times the hours. The full write-up is in [writeup.pdf](writeup.pdf).

Senan Tubridy, Boston, November 2026.

## What's here

| File | What it does |
| --- | --- |
| [writeup.pdf](writeup.pdf) | Two-page write-up with sources ([writeup.md](writeup.md) is the text) |
| [replay.html](replay.html) | Interactive replay of winter 2020/21: one launch a day from each site, drifting or steered. Open it in a browser. |
| [balloon.py](balloon.py) | The model: wind interpolation, RK4 integrator (lat/lon and pole-safe 3D), the gap, greedy steering |
| `01_winds_stations_integrator.ipynb` | Loads winds and stations, draws the gap, tests the integrator on an exact rotation |
| `02_passive_gap_hours.ipynb` | Drifting balloons: every winter day, five sites, three heights, 21 days |
| `03_checks_wide_box_and_arctic.ipynb` | Checks: a wider box, and the Atlantic vs Arctic split |
| `04_steered.ipynb` | Steering, bracketed by a no-look-ahead pilot and a perfect-look-ahead pilot |
| `05_sensitivity_no_250hPa.ipynb` | The same without 250 hPa (inside FL300 to FL400) |
| [decisions.md](decisions.md) | Every method choice and why |
| [limitations.md](limitations.md) | Everything the model leaves out |
| `passive_runs.csv`, `checks_runs.csv`, `steered_runs.csv`, `steered_no250_runs.csv` | Per-launch results |
| `fig1_drift_paths.png`, `fig2_gap_hours.png` | The two figures in the write-up |
| `make_figures.py`, `make_replay_data.py`, `build_pdf.py` | Rebuild the figures, the replay page (from `template.html`) and the PDF |

## The method in brief

- **Winds:** ERA5 reanalysis, 1.5°, every 6 hours, from the WeatherBench 2 copy on Google Cloud. It's read anonymously; no account is needed.
- **Launches:** one balloon a day from Egilsstaðir, Keflavík, Cambridge MA, a New York stand-in point and Juneau, every winter day from Dec 2013 to Feb 2022. Each flies 21 days.
- **Model:** dφ/dt = v/R, dλ/dt = u/(R cos φ), solved with RK4 in 1-hour steps. A 3D version handles flights over the pole. Both are tested against an exact solid-body rotation and converge at 4th order.
- **The gap:** more than 500 km from any active radiosonde station (NOAA IGRA2, plus Keflavík and Egilsstaðir from the Icelandic AIP), inside 45 to 90°N, 70°W to 30°E. 300 and 800 km are run as checks.

## Running it

1. Install Anaconda, then create the environment:
   `conda env create -f environment.yml` and `conda activate windborne`
2. Run the notebooks in order (01 to 05) in Jupyter. Notebook 02 downloads about 3 GB of winds the first time.
3. Optional: `python make_figures.py`, `python make_replay_data.py`, `python build_pdf.py`. The PDF script uses the Arial font from macOS.

## How this was made

Claude (Anthropic's AI) wrote the code to my spec. I chose the method, checked it, and wrote down where it breaks.
