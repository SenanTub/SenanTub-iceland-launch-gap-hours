"""
make_replay_data.py: precompute one winter of virtual launches for the replay page.

Flies one balloon a day from each site (1 Dec 2020 to 28 Feb 2021), each for 21 days,
in four modes, then writes everything the page needs (tracks, gap-hours, the gap, coastlines)
into replay.html. All the physics happens here; the page only plays it back.

Run from the project folder:  python make_replay_data.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import cartopy.io.shapereader as shpreader

import balloon as b

WINTER = 2020                                   # December year: winter 2020/21
STEP_H = 6                                      # store positions every 6 hours
SITES = {                                       # name: (lat, lon, colour)
    "Egilsstaðir":  (65.28, -14.40, "#2a78d6"),
    "Keflavík":     (63.97, -22.60, "#eb6834"),
    "New York*":    (40.71, -74.01, "#1baf7a"),
    "Cambridge MA": (42.36, -71.09, "#eda100"),
    "Juneau":       (58.30, -134.42, "#e87ba4"),
}
names = list(SITES)

# ---- winds and launches
w = b.load_winter(WINTER)
wind850 = b.make_wind(w["u"][:, 0], w["v"][:, 0], w["time"])
wind500 = b.make_wind(w["u"][:, 1], w["v"][:, 1], w["time"])
days = pd.date_range(f"{WINTER}-12-01", f"{WINTER + 1}-03-01", freq="D", inclusive="left")
site_idx = np.tile(np.arange(len(names)), len(days))
day_idx = np.repeat(np.arange(len(days)), len(names))
lat0 = np.array([SITES[n][0] for n in names])[site_idx]
lon0 = np.array([SITES[n][1] for n in names])[site_idx]
t0 = (days.values[day_idx] - w["time"][0]) / np.timedelta64(1, "s")

# ---- the 500 km gap (same definition as notebooks 02 to 05)
stations = b.active_stations()
gap = b.nearest_station_km_grid(stations) > 500
region_lats, region_lons = b.region_grid()

# ---- fly all four modes (steering uses 850 and 500 hPa only, as in the write-up)
H = 21 * 24
modes = {}
_, la, lo = b.fly_xyz(wind850, lat0, lon0, t0, H); modes["drift850"] = (la, lo)
_, la, lo = b.fly_xyz(wind500, lat0, lon0, t0, H); modes["drift500"] = (la, lo)
for look in ["persistence", "perfect"]:
    la, lo, _ = b.fly_steered([wind850, wind500], lat0, lon0, t0, H, gap,
                              tiebreak="closest", lookahead=look, start_level=1)
    modes[f"steer_{look}"] = (la, lo)


def pack(mode_lats, mode_lons):
    # Per site, per launch day: positions every STEP_H hours (lat, lon x10 as ints)
    # and cumulative gap-hours (counted hourly) at those same times.
    inside = b.in_gap(mode_lats[1:], mode_lons[1:], gap)               # (H, n) hourly
    cum = np.concatenate([np.zeros((1, inside.shape[1])), np.cumsum(inside, axis=0)])
    tracks, gapcum = [], []
    for s in range(len(names)):
        cols = np.where(site_idx == s)[0]                              # one per launch day
        t_s, g_s = [], []
        for c in cols:
            la_ = np.round(mode_lats[::STEP_H, c] * 10).astype(int)
            lo_ = np.round(mode_lons[::STEP_H, c] * 10).astype(int)
            t_s.append(np.column_stack([la_, lo_]).ravel().tolist())
            g_s.append(cum[::STEP_H, c].astype(int).tolist())
        tracks.append(t_s); gapcum.append(g_s)
    return tracks, gapcum


data = {
    "sites": [dict(name=n, lat=SITES[n][0], lon=SITES[n][1], colour=SITES[n][2]) for n in names],
    "start": str(days[0].date()), "n_days": len(days), "step_h": STEP_H, "track_len": H // STEP_H + 1,
    "region": dict(lat0=float(region_lats[0]), lon0=float(region_lons[0]), step=b.GRID_STEP,
                   n_lat=len(region_lats), n_lon=len(region_lons),
                   mask="".join("1" if v else "0" for v in gap.ravel())),
    "modes": {},
}
for m, (la, lo) in modes.items():
    tr, gc = pack(la, lo)
    data["modes"][m] = dict(tracks=tr, gapcum=gc)

# ---- coastlines north of 20N (Natural Earth 110m, via cartopy)
coast = []
for geom in shpreader.Reader(shpreader.natural_earth("110m", "physical", "coastline")).geometries():
    for line in getattr(geom, "geoms", [geom]):
        xy = np.array(line.coords)
        keep = xy[:, 1] > 20
        if keep.sum() > 1:
            coast.append(np.round(xy[keep][:, ::-1], 1).ravel().tolist())     # [lat, lon, ...]
data["coast"] = coast
# active radiosonde stations north of 20N, for context on the map
st = stations[stations.lat > 20]
data["stations"] = np.round(st[["lat", "lon"]].values, 1).ravel().tolist()

# ---- write the page: template + data in one self-contained file
template = Path("template.html").read_text()
page = template.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
Path("replay.html").write_text(page)
print("wrote replay.html,", round(len(page) / 1e6, 2), "MB")
for m, (la, lo) in modes.items():
    med = {n: float(np.median(b.in_gap(la[1:], lo[1:], gap).sum(0)[site_idx == i])) for i, n in enumerate(names)}
    print(m, "median gap-hours per launch:", med)
