"""
prepare_github_folder.py: copy only the public files into ../windborne-iceland-github,
ready to drag into GitHub's "Upload files" page. Private notes (CLAUDE.md, the copy of the
Iceland proposal, Claude settings) and the 2.6 GB of downloaded winds are left out on purpose.
Run it again after re-running the notebooks, so the uploaded copies include their outputs.
"""
import shutil
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent / "windborne-iceland-github"
PUBLIC = [
    "README.md", "writeup.md", "writeup.pdf", "Iceland_Launch_Site_Assessment_Senan_Tubridy.pdf",
    "make_brief.py", "brief_map.png", "brief_chart_gap_hours.png", "brief_chart_arctic_weather.png", "decisions.md", "limitations.md", "environment.yml",
    "balloon.py", "make_figures.py", "make_replay_data.py", "build_pdf.py", "prepare_github_folder.py",
    "01_winds_stations_integrator.ipynb", "02_passive_gap_hours.ipynb",
    "03_checks_wide_box_and_arctic.ipynb", "04_steered.ipynb", "05_sensitivity_no_250hPa.ipynb",
    "fig1_drift_paths.png", "fig2_gap_hours.png", "passive_runs.csv", "checks_runs.csv",
    "steered_runs.csv", "steered_no250_runs.csv", "replay.html", "template.html",
]

if OUT.exists():
    shutil.rmtree(OUT)
for item in PUBLIC:
    src, dst = HERE / item, OUT / item
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
print("copied", len(PUBLIC), "items to", OUT)
