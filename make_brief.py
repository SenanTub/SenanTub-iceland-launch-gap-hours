"""
make_brief.py: the two-page brief "Iceland as a WindBorne launch site", with its charts.

Reads the saved results (notebooks 02 and 05) and fig1_drift_paths.png (make_figures.py),
draws two more charts, and lays everything out as a US-letter PDF.
Run from the project folder:  python make_brief.py
"""
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

import build_pdf  # registers the Arial fonts

OUT = "Iceland_Launch_Site_Assessment_Senan_Tubridy.pdf"
REPO = "github.com/SenanTub/SenanTub-iceland-launch-gap-hours"
REPLAY = "senantub.github.io/SenanTub-iceland-launch-gap-hours/replay.html"

SITES = ["Egilsstaðir", "Keflavík", "New York*", "Cambridge MA", "Juneau"]
COLOURS = dict(zip(SITES, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
INK, INK2, GREY = "#16202a", "#4a5663", "#8a8984"
matplotlib.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.edgecolor": "#b9c2ca",
                            "xtick.color": INK2, "ytick.color": INK2, "axes.labelcolor": INK2})

# ---------------------------------------------------------------- data
passive = pd.read_csv("passive_runs.csv")
steer = pd.read_csv("steered_no250_runs.csv")
steer = steer[(steer.gap_km == 500) & (steer.tiebreak == "closest")].copy()
steer["atlantic_21d"] = steer.gap_21d - steer.arctic_21d

drift_med = passive[passive.level == 500].groupby("site").gap_h_500km_21d.median()
steer_med = steer.groupby(["site", "lookahead"]).gap_21d.median().unstack()       # persistence, perfect
parts = steer.groupby("site")[["atlantic_21d", "arctic_21d"]].mean()            # both pilots pooled

# ---------------------------------------------------------------- chart A: gap-hours per launch
order = steer_med.mean(axis=1).sort_values().index.tolist()                      # lowest at the bottom
fig, ax = plt.subplots(figsize=(7.0, 2.1))
for y, site in enumerate(order):
    lo, hi = steer_med.loc[site, "persistence"], steer_med.loc[site, "perfect"]
    width = max(hi - lo, 0.8)                                   # equal values still get a visible mark
    ax.barh(y, width, left=lo - (width - (hi - lo)) / 2, height=0.5, color=COLOURS[site])
    ax.plot(drift_med[site], y, "o", color=GREY, ms=7, markeredgecolor="white", markeredgewidth=1.5)
    ax.text(hi + 1.5, y, f"{lo:g} to {hi:g} h" if lo != hi else f"{hi:g} h", va="center", fontsize=8, color=INK)
    ax.text(drift_med[site] - 1.5, y, f"{drift_med[site]:g}", va="center", ha="right", fontsize=8, color=INK2)
ax.set_yticks(range(len(order)), order, fontsize=9, color=INK)
ax.set_xlim(0, 70)
ax.set_xlabel("median hours in the gap per launch, over a 21-day flight")
ax.grid(axis="x", color="#e7ebee"); ax.set_axisbelow(True)
for s in ["top", "right", "left"]: ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
handles = [Line2D([], [], marker="o", ls="", color=GREY, label="drifting at 500 hPa"),
           Patch(color="#52514e", label="steered, range from no look-ahead to perfect look-ahead")]
ax.legend(handles=handles, frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
fig.savefig("brief_chart_gap_hours.png", dpi=240, bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- map: Egilsstaðir vs Cambridge
import cartopy.crs as ccrs
import balloon as b
stations = b.active_stations()
gap = b.nearest_station_km_grid(stations) > 500
region_lats, region_lons = b.region_grid()
pair = {"Egilsstaðir": (65.28, -14.40), "Cambridge MA": (42.36, -71.09)}
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), subplot_kw=dict(projection=ccrs.NorthPolarStereo(central_longitude=-40)))
for ax, site in zip(axes, pair):
    ax.set_extent([-95, 45, 33, 90], crs=ccrs.PlateCarree())
    ax.pcolormesh(region_lons, region_lats, np.where(gap, 1.0, np.nan), transform=ccrs.PlateCarree(),
                  cmap="Greys", vmin=0, vmax=2.6, shading="auto", zorder=1)
    ax.coastlines(color="#9aa7b3", lw=0.5, zorder=2)
    ax.scatter(stations.lon, stations.lat, s=1.5, color="#6b7785", transform=ccrs.PlateCarree(), zorder=3)
    for winter in range(2013, 2022):
        lats, lons, _, _ = b.fly_winter(winter, {site: pair[site]}, level_index=1, hours=7 * 24)
        for i in range(0, lats.shape[1], 6):
            ax.plot(lons[:, i], lats[:, i], color=COLOURS[site], lw=0.4, alpha=0.5, transform=ccrs.Geodetic(), zorder=4)
    ax.plot(pair[site][1], pair[site][0], marker="^", color="black", ms=7, transform=ccrs.PlateCarree(), zorder=5)
    ax.set_title(site, fontsize=9.5, color=INK)
    ax.spines["geo"].set_edgecolor("#c9d2da")
fig.savefig("brief_map.png", dpi=240, bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- chart B: Atlantic vs Arctic, and launch weather
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.3), gridspec_kw=dict(width_ratios=[1.25, 1], wspace=0.55))
for y, site in enumerate(SITES[::-1]):
    a, r = parts.loc[site, "atlantic_21d"], parts.loc[site, "arctic_21d"]
    ax1.barh(y, a, color="#c9d2da", height=0.62)
    ax1.barh(y, r, left=a, color=COLOURS[site], height=0.62, edgecolor="white", linewidth=1.5)
    ax1.text(a + r + 1.2, y, f"{r:.0f} Arctic", va="center", fontsize=8, color=INK)
ax1.set_yticks(range(len(SITES)), SITES[::-1], fontsize=9, color=INK)
ax1.set_xlim(0, 85); ax1.tick_params(axis="y", length=0)
ax1.set_xlabel("mean gap-hours per steered launch")
ax1.set_title("Grey: Atlantic part (45 to 60°N)   Colour: Arctic part (60 to 90°N)", fontsize=8, color=INK2, loc="left")
for s in ["top", "right", "left"]: ax1.spines[s].set_visible(False)

weather = [("Egilsstaðir", 78), ("Akureyri", 71), ("Höfn", 67), ("Juneau (existing)", 62), ("Keflavík", 57)]
for y, (name, pct) in enumerate(weather[::-1]):
    col = "#8a8984" if name.startswith("Juneau") else "#2a5d8a"
    ax2.barh(y, pct, color=col, height=0.62)
    ax2.text(pct + 1.5, y, f"{pct}%", va="center", fontsize=8, color=INK)
ax2.axvline(62, color="#8a8984", lw=1, ls=":")
ax2.set_yticks(range(len(weather)), [w[0] for w in weather[::-1]], fontsize=9, color=INK)
ax2.set_xlim(0, 100); ax2.tick_params(axis="y", length=0)
ax2.set_xlabel("winter days with a calm, dry 3-hour window")
ax2.set_title("Launch weather, strict limit (ERA5)", fontsize=8, color=INK2, loc="left")
for s in ["top", "right", "left"]: ax2.spines[s].set_visible(False)
fig.savefig("brief_chart_arctic_weather.png", dpi=240, bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- PDF
ACCENT = colors.HexColor("#1f4e79")
TINT = colors.HexColor("#eef3f8")
body = ParagraphStyle("b", fontName="Arial", fontSize=8.9, leading=11.6, textColor=colors.HexColor(INK), spaceAfter=3)
small = ParagraphStyle("s", parent=body, fontSize=7.3, leading=9.2, textColor=colors.HexColor(INK2), spaceAfter=1.5)
h2 = ParagraphStyle("h2", parent=body, fontName="Arial-Bold", fontSize=10.5, leading=13, textColor=ACCENT,
                    spaceBefore=7, spaceAfter=3)
label = ParagraphStyle("lab", parent=body, fontName="Arial-Bold", fontSize=7.5, leading=9,
                       textColor=ACCENT, spaceAfter=1)
big = ParagraphStyle("big", parent=body, fontName="Arial-Bold", fontSize=17, leading=19, textColor=colors.HexColor(INK))
tile_txt = ParagraphStyle("tt", parent=body, fontSize=7.8, leading=9.6, textColor=colors.HexColor(INK2))
cell = ParagraphStyle("c", parent=body, fontSize=8.1, leading=10, spaceAfter=0)
cap = ParagraphStyle("cap", parent=small, spaceAfter=6)
W = 7.0 * inch


def img(path, width, caption=None):
    im = Image(path)
    im.drawWidth, im.drawHeight = width, width * im.imageHeight / im.imageWidth
    parts_ = [im] + ([Paragraph(caption, cap)] if caption else [])
    return KeepTogether(parts_)


def box(flowables, bg=TINT, pad=8):
    t = Table([[flowables]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LEFTPADDING", (0, 0), (-1, -1), pad),
                           ("RIGHTPADDING", (0, 0), (-1, -1), pad), ("TOPPADDING", (0, 0), (-1, -1), pad - 2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 2)]))
    return t


def tiles(items):
    cells = [[Paragraph(n, big), Spacer(1, 2), Paragraph(t, tile_txt)] for n, t in items]
    t = Table([cells], colWidths=[W / 3] * 3)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.white),
                           ("LINEABOVE", (0, 0), (-1, 0), 2, ACCENT),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def header(canvas, doc):
    canvas.saveState()
    w, h = letter
    if doc.page == 1:
        canvas.setFillColor(ACCENT); canvas.rect(0, h - 1.05 * inch, w, 1.05 * inch, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Arial-Bold", 19); canvas.drawString(0.75 * inch, h - 0.55 * inch, "Iceland as a WindBorne launch site")
        canvas.setFont("Arial", 9.5)
        canvas.drawString(0.75 * inch, h - 0.82 * inch,
                          "An assessment with reanalysis winds  ·  Senan Tubridy  ·  November 2026")
    canvas.setFont("Arial", 7.3); canvas.setFillColor(colors.HexColor(INK2))
    canvas.drawString(0.75 * inch, 0.42 * inch, f"Code and data: {REPO}")
    canvas.drawRightString(w - 0.75 * inch, 0.42 * inch, f"{doc.page} of 2")
    canvas.restoreState()


story = [
    Paragraph("THE QUESTION", label),
    Paragraph("<b>Would a launch site in Iceland put more balloon time over the thinly observed North Atlantic "
              "and Arctic than launches from WindBorne's existing sites?</b> WindBorne lists Iceland among its "
              "candidate sites for the next 18 months [1], and balloons from existing sites already reach the "
              "Arctic [2]. The useful number is what one Iceland launch adds.", body),
    Spacer(1, 4),
    box([Paragraph("THE ANSWER", label),
         Paragraph("<b>Not for the North Atlantic, and only modestly for the Arctic.</b> Per launch, a balloon from "
                   "Egilsstaðir or Keflavík spends less time in the observing gap than one from Cambridge MA or "
                   "New York, drifting or steered. Iceland's balloons reach the Arctic part of the gap more often, "
                   "but Juneau, an existing site, already matches them there.", body)]),
    Spacer(1, 7),
    tiles([("12 h vs 20 h", "median gap-hours per drifting launch over 21 days: Egilsstaðir vs Cambridge MA"),
           ("4th or 5th of 5", "rank of both Iceland sites at 500 and 800 km gap sizes, under every steering case"),
           ("1.3 to 1.4×", "Arctic gap-hours per steered Iceland launch vs a US launch; Juneau is level with Iceland")]),
    Paragraph("WHY: WHERE THE BALLOONS GO", ParagraphStyle("h2b", parent=h2, fontSize=8, textColor=ACCENT)),
    img("brief_map.png", 6.3 * inch,
        "First 7 days of drift at 500 hPa, every 6th daily launch, nine winters. Grey: the gap, more than 500 km "
        "from any active radiosonde station [3, 4] inside 45 to 90°N, 70°W to 30°E. Iceland is ringed by stations; "
        "its balloons scatter east over well-observed Norway. Cambridge balloons cross the open Atlantic gap within a day."),
    img("brief_chart_gap_hours.png", W,
        "Gap-hours per launch, 812 launches per site (every winter day, Dec 2013 to Feb 2022, ERA5 winds [5, 6]). "
        "Steered balloons choose 850 or 500 hPa every 6 hours; the bar spans a pilot with no look-ahead and one with "
        "a perfect 6-hour forecast. 250 hPa is excluded as it lies in the FL300 to FL400 band WindBorne no longer "
        "floats in [7]."),
    KeepTogether([Paragraph("WHAT STILL FAVOURS ICELAND", ParagraphStyle("h2c", parent=h2, fontSize=8, textColor=ACCENT)),
    img("brief_chart_arctic_weather.png", W,
        "Left: steered gap-hours split at 60°N; Iceland's hours lean Arctic, but Juneau matches them there. "
        "Right: share of Dec to Feb days with 3+ hours of wind under 6 m/s, gusts under 10 m/s and no rain "
        "(ERA5, 2016 to 2025 [8]). The north and east of Iceland beat Juneau, which already works. Limits are "
        "placeholders; ERA5's 30 km cells smooth out valleys, as St Helena's relocated launches showed [9].")]),
    Paragraph("Egilsstaðir and Akureyri also sit outside the Keflavík approach area (up to 24,500 ft, about 40 NM "
              "out) [10] and away from the Reykjanes eruptions [11]. Any site needs Icelandic Transport Authority "
              "permission for unmanned free balloons [12].", body),
    Paragraph("OPEN QUESTIONS", ParagraphStyle("h2d", parent=h2, fontSize=8, textColor=ACCENT)),
]

q_rows = [["Question", "Who can answer"],
          ["Is about a third more Arctic time per launch than a US site worth a new site, given Juneau?", "WindBorne"],
          ["How much of the fleet already flies north of 60°N, and at what altitudes?", "WindBorne flight logs"],
          ["How often does wind stop the Keflavík and Egilsstaðir soundings, and at what speed?", "Icelandic Met Office"],
          ["What does permission for repeated launches involve, and how long does it take?", "Icelandic Transport Authority"],
          ["Can lift gas be supplied outside Reykjavík, and with what lead time?", "Gas suppliers (e.g. Linde)"]]
qt = Table([[Paragraph(c, cell) for c in r] for r in q_rows], colWidths=[5.0 * inch, 2.0 * inch])
qt.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT), ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#d9e0e6")),
                        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 2), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
story += [qt, Spacer(1, 4),
          Paragraph("LIMITS", ParagraphStyle("h2e", parent=h2, fontSize=8, textColor=ACCENT)),
          Paragraph("The gap counts radiosondes only, not aircraft, satellites or WindBorne's own fleet. Each site is "
                    "judged alone. The steering pilots are simple stand-ins (two heights, instant changes, unlimited "
                    "ballast), not WindBorne's navigation. At a looser 300 km gap, Keflavík moves into the top three. "
                    "WindBorne's flight logs would settle all four; the same method runs on them directly.", body),
          Paragraph(f"Interactive replay of winter 2020/21: {REPLAY}. Code written with Claude to the author's "
                    "specification; method choices, checks and limits are the author's.", small),
          Spacer(1, 4)]

refs = [
    "WindBorne Systems, Field Operations Specialist posting, 5 Jun 2026.",
    "Spisak et al. (2026), arXiv:2602.02714.",
    "Durre, I. et al. (2018), Enhancing the data coverage in the Integrated Global Radiosonde Archive, J. Atmos. Oceanic Technol. 35.",
    "AIP Iceland GEN 3.5 and ENR 5.3 (Keflavík and Egilsstaðir soundings, added because IGRA2 omits them).",
    "Hersbach, H. et al. (2020), The ERA5 global reanalysis, Q. J. R. Meteorol. Soc. 146.",
    "Rasp, S. et al. (2024), WeatherBench 2, J. Adv. Model. Earth Syst. 16.",
    "WindBorne Systems, UA1093 update.",
    "Open-Meteo historical weather API, ERA5, hourly 10 m wind, gusts and precipitation, 2016 to 2025.",
    "St Helena Government, notice on WindBorne trial launches, 30 Jun 2026.",
    "Isavia ANS, Keflavík approach area.",
    "AIP Iceland SUP 11/2024 (Grindavík eruptions).",
    "AIP Iceland ENR 1.1.10; regulation 770/2010, appendix 4.",
]
story.append(Paragraph("References: " + "  ".join(f"[{i}] {r}" for i, r in enumerate(refs, 1)), small))

# page 2 has no header band, so it gets a smaller top margin
from reportlab.platypus import Frame, PageTemplate, NextPageTemplate
doc = SimpleDocTemplate(OUT, pagesize=letter, title="Iceland as a WindBorne launch site", author="Senan Tubridy")
f1 = Frame(0.75 * inch, 0.65 * inch, W, letter[1] - 1.25 * inch - 0.65 * inch, id="f1", leftPadding=0, rightPadding=0)
f2 = Frame(0.75 * inch, 0.65 * inch, W, letter[1] - 0.6 * inch - 0.65 * inch, id="f2", leftPadding=0, rightPadding=0)
doc.addPageTemplates([PageTemplate("first", [f1], onPage=header), PageTemplate("rest", [f2], onPage=header)])
story.insert(0, NextPageTemplate("rest"))
doc.build(story)
print("wrote", OUT)
