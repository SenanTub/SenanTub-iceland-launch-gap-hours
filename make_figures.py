"""
make_figures.py: the two figures for the write-up, from saved results.

Figure 1: where 7 days of drift at 500 hPa takes balloons from Egilsstaðir vs Cambridge MA.
Figure 2: gap-hours per launch by site, drifting vs the steering bracket (850 and 500 hPa).
Run from the project folder after notebooks 02 and 05:  python make_figures.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import balloon as b

plt.rcParams.update({"font.family": "sans-serif", "font.size": 9, "axes.edgecolor": "#8a8984",
                     "axes.labelcolor": "#2b2b2b", "xtick.color": "#52514e", "ytick.color": "#52514e"})

SITES = {
    "Egilsstaðir":  (65.28, -14.40),
    "Keflavík":     (63.97, -22.60),
    "New York*":    (40.71, -74.01),
    "Cambridge MA": (42.36, -71.09),
    "Juneau":       (58.30, -134.42),
}
COLOURS = dict(zip(SITES, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
order = list(SITES)

stations = b.active_stations()
gap = b.nearest_station_km_grid(stations) > 500
region_lats, region_lons = b.region_grid()

# ---------------------------------------------------------------- Figure 1
pair = {"Egilsstaðir": SITES["Egilsstaðir"], "Cambridge MA": SITES["Cambridge MA"]}
proj = ccrs.NorthPolarStereo(central_longitude=-40)
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6), subplot_kw=dict(projection=proj))
for ax, site in zip(axes, pair):
    ax.set_extent([-95, 45, 33, 90], crs=ccrs.PlateCarree())
    ax.pcolormesh(region_lons, region_lats, np.where(gap, 1.0, np.nan), transform=ccrs.PlateCarree(),
                  cmap="Greys", vmin=0, vmax=2.6, shading="auto", zorder=1)
    ax.coastlines(color="#9aa7b3", lw=0.5, zorder=2)
    ax.scatter(stations.lon, stations.lat, s=2, color="#6b7785", transform=ccrs.PlateCarree(), zorder=3)
    for winter in range(2013, 2022):
        lats, lons, names, _ = b.fly_winter(winter, {site: pair[site]}, level_index=1, hours=7 * 24)
        for i in range(0, lats.shape[1], 6):                      # every 6th launch day
            ax.plot(lons[:, i], lats[:, i], color=COLOURS[site], lw=0.45, alpha=0.5,
                    transform=ccrs.Geodetic(), zorder=4)
    ax.plot(pair[site][1], pair[site][0], marker="^", color="black", ms=7,
            transform=ccrs.PlateCarree(), zorder=5)
    ax.set_title(site, fontsize=10, color="#2b2b2b")
fig.suptitle("Where balloons drift in their first 7 days (500 hPa, winters 2013/14 to 2021/22)",
             fontsize=10, color="#2b2b2b", y=0.98)
fig.savefig("fig1_drift_paths.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- Figure 2
passive = pd.read_csv("passive_runs.csv")
steer = pd.read_csv("steered_no250_runs.csv")
steer = steer[(steer.gap_km == 500) & (steer.tiebreak == "closest")]

fig, ax = plt.subplots(figsize=(7.2, 3.2))
variants = [("Drifting at 500 hPa", "o", None, True),
            ("Steered, no look-ahead", "s", "persistence", False),
            ("Steered, perfect 6 h look-ahead", "D", "perfect", True)]
for vi, (label, marker, look, filled) in enumerate(variants):
    for si, site in enumerate(order):
        if look is None:
            x = passive[(passive.level == 500) & (passive.site == site)].gap_h_500km_21d
            colour = "#8a8984"
        else:
            x = steer[(steer.lookahead == look) & (steer.site == site)].gap_21d
            colour = COLOURS[site]
        xpos = si + (vi - 1) * 0.24
        ax.plot([xpos, xpos], np.percentile(x, [25, 75]), color=colour, lw=2, solid_capstyle="round")
        ax.plot(xpos, np.median(x), marker=marker, ms=7, color=colour,
                markerfacecolor=colour if filled else "white", markeredgewidth=1.6,
                label=label if si == 0 else None)
        ax.annotate(f"{np.median(x):g}", (xpos, np.median(x)), xytext=(6, 0),
                    textcoords="offset points", ha="left", va="center", fontsize=7, color="#52514e")
ax.set_xticks(range(len(order)), order)
ax.set_ylabel("hours in the gap per launch\n(21 days, 500 km gap)")
ax.grid(axis="y", color="#e5e5e5"); ax.set_axisbelow(True)
for side in ["top", "right"]: ax.spines[side].set_visible(False)
leg = ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8)
for h, v in zip(leg.legend_handles, variants):
    h.set_color("#52514e"); h.set_markerfacecolor("#52514e" if v[3] else "white")
ax.set_title("Gap-hours per launch: marker = median, bar = middle half of launches (about 800 per site)",
             fontsize=9, color="#2b2b2b")
fig.savefig("fig2_gap_hours.png", dpi=220, bbox_inches="tight")
plt.close(fig)
print("wrote fig1_drift_paths.png and fig2_gap_hours.png")
