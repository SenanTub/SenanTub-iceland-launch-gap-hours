"""
balloon.py: shared functions for "What one Iceland launch buys".

Notebook 01 explains and tests each of these step by step. They live here so
later notebooks use exactly one copy. Two differences from notebook 01:
  * fly() accepts a different launch time for every balloon, so a whole winter
    of daily launches can be flown in one go.
  * make_wind() accepts a different time for every balloon for the same reason.
"""
from pathlib import Path
import urllib.request

import numpy as np
import pandas as pd
import xarray as xr

R_EARTH = 6_371_000.0          # Earth's mean radius, metres
DATA = Path(__file__).parent / "data"

WIND_STORE = ("gs://weatherbench2/datasets/era5/"
              "1959-2023_01_10-6h-240x121_equiangular_with_poles_conservative.zarr")
LEVELS = [850, 500, 250]       # hPa (decisions.md)

# The gap region (decisions.md): 45 to 90N, 70W to 30E, on the 1.5 degree wind grid
GAP_LAT_MIN, GAP_LAT_MAX = 45.0, 90.0
GAP_LON_MIN, GAP_LON_MAX = -70.0, 30.0
GRID_STEP = 1.5


# ---------------------------------------------------------------- geometry

def wrap_lon(lon_deg):
    """Keep longitude in [-180, 180) so the dateline doesn't break anything."""
    return (lon_deg + 180.0) % 360.0 - 180.0


def great_circle_km(lat1, lon1, lat2, lon2):
    """Haversine distance in km between points in degrees (works on arrays)."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * R_EARTH / 1000 * np.arcsin(np.sqrt(a))


# ---------------------------------------------------------------- integrator

def drift_rate(lat_deg, u, v):
    """d(lat)/dt and d(lon)/dt in degrees per second for wind u (east), v (north) in m/s.
    dphi/dt = v / R,  dlambda/dt = u / (R cos phi)."""
    lat = np.radians(lat_deg)
    dlat_dt = v / R_EARTH
    dlon_dt = u / (R_EARTH * np.cos(lat))     # longitude circles shrink by cos(lat)
    return np.degrees(dlat_dt), np.degrees(dlon_dt)


def rk4_step(wind, t, lat, lon, dt):
    """One classical Runge-Kutta step of length dt seconds. wind(t, lat, lon) -> (u, v)."""
    def f(t, lat, lon):
        u, v = wind(t, lat, lon)
        return drift_rate(lat, u, v)

    k1 = f(t,          lat,                  lon)
    k2 = f(t + dt / 2, lat + dt / 2 * k1[0], lon + dt / 2 * k1[1])
    k3 = f(t + dt / 2, lat + dt / 2 * k2[0], lon + dt / 2 * k2[1])
    k4 = f(t + dt,     lat + dt * k3[0],     lon + dt * k3[1])

    new_lat = lat + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
    new_lon = lon + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
    return new_lat, wrap_lon(new_lon)


def fly(wind, lat0, lon0, t0, hours, dt_hours=1.0, pole_stop=88.0):
    """Fly many balloons. lat0, lon0, t0 can be arrays (one entry per balloon);
    t0 is each balloon's launch time in seconds on the wind data's clock.
    Returns (hours_since_launch, lats, lons) with lats/lons of shape (n_steps+1, n_balloons).
    A balloon that passes pole_stop degrees latitude is stopped (NaN from then on),
    because dlon/dt blows up as cos(lat) -> 0."""
    lat = np.atleast_1d(np.asarray(lat0, dtype=float)).copy()
    lon = np.atleast_1d(np.asarray(lon0, dtype=float)).copy()
    t0 = np.broadcast_to(np.asarray(t0, dtype=float), lat.shape)
    dt = dt_hours * 3600.0
    n_steps = int(round(hours / dt_hours))

    lats = np.full((n_steps + 1, lat.size), np.nan)
    lons = np.full((n_steps + 1, lat.size), np.nan)
    lats[0], lons[0] = lat, lon
    alive = np.abs(lat) < pole_stop

    for i in range(n_steps):
        if alive.any():
            t = t0[alive] + i * dt
            lat[alive], lon[alive] = rk4_step(wind, t, lat[alive], lon[alive], dt)
        alive &= np.abs(lat) < pole_stop
        lats[i + 1, alive], lons[i + 1, alive] = lat[alive], lon[alive]

    return np.arange(n_steps + 1) * dt_hours, lats, lons


# ---------------------------------------------------------------- pole-safe integrator (3D)
# The lat/lon equations divide by cos(lat), which is 0 at the pole. Instead we can track
# the balloon as a point (x, y, z) on a unit sphere. Its velocity is the wind vector
#   (u * east + v * north) / R
# where east and north are unit vectors at the balloon's position. Nothing divides by
# cos(lat), so balloons can fly straight over the pole. After each RK4 step we rescale
# the point back onto the sphere (it drifts off very slightly because steps are straight).

def to_xyz(lat_deg, lon_deg):
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    return np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])


def to_latlon(xyz):
    x, y, z = xyz
    return np.degrees(np.arctan2(z, np.hypot(x, y))), np.degrees(np.arctan2(y, x))


def velocity_xyz(wind, t, xyz):
    # Rate of change of the unit position vector (per second)
    lat_deg, lon_deg = to_latlon(xyz)
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    east = np.array([-np.sin(lon), np.cos(lon), np.zeros_like(lon)])
    north = np.array([-np.sin(lat) * np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat)])
    u, v = wind(t, lat_deg, lon_deg)
    return (u * east + v * north) / R_EARTH


def rk4_step_xyz(wind, t, lat, lon, dt):
    """Same RK4 as rk4_step, but on the 3D position. Takes and returns lat/lon in degrees."""
    r = to_xyz(lat, lon)
    k1 = velocity_xyz(wind, t, r)
    k2 = velocity_xyz(wind, t + dt / 2, r + dt / 2 * k1)
    k3 = velocity_xyz(wind, t + dt / 2, r + dt / 2 * k2)
    k4 = velocity_xyz(wind, t + dt, r + dt * k3)
    r_new = r + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    r_new /= np.linalg.norm(r_new, axis=0)       # put it back on the sphere
    return to_latlon(r_new)


def fly_xyz(wind, lat0, lon0, t0, hours, dt_hours=1.0):
    """Like fly(), but pole-safe: uses rk4_step_xyz and never stops a balloon."""
    lat = np.atleast_1d(np.asarray(lat0, dtype=float)).copy()
    lon = np.atleast_1d(np.asarray(lon0, dtype=float)).copy()
    t0 = np.broadcast_to(np.asarray(t0, dtype=float), lat.shape)
    dt = dt_hours * 3600.0
    n_steps = int(round(hours / dt_hours))
    lats = np.empty((n_steps + 1, lat.size)); lons = np.empty((n_steps + 1, lat.size))
    lats[0], lons[0] = lat, lon
    for i in range(n_steps):
        lat, lon = rk4_step_xyz(wind, t0 + i * dt, lat, lon, dt)
        lats[i + 1], lons[i + 1] = lat, lon
    return np.arange(n_steps + 1) * dt_hours, lats, lons


# ---------------------------------------------------------------- winds

def open_era5():
    """Open the WeatherBench2 ERA5 store (index only; numbers download on demand)."""
    return xr.open_zarr(WIND_STORE, storage_options=dict(token="anon"), chunks=None)


def winter_file(dec_year):
    return DATA / "winds" / f"era5_winter_{dec_year}.npz"


def download_winter(era5, dec_year):
    """Save u and v at LEVELS from 1 Dec to 22 Mar (21 days after the last Feb launch)
    for the winter starting in December of dec_year. About 300 MB per winter."""
    path = winter_file(dec_year)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    block = era5[["u_component_of_wind", "v_component_of_wind"]].sel(
        time=slice(f"{dec_year}-12-01", f"{dec_year + 1}-03-22T18"), level=LEVELS).load()
    np.savez(path,
             u=block["u_component_of_wind"].values.astype(np.float32),   # (time, level, lon, lat)
             v=block["v_component_of_wind"].values.astype(np.float32),
             time=block.time.values, levels=np.array(LEVELS))
    return path


def load_winter(dec_year):
    """Load one saved winter: dict with u, v (time, level, lon, lat), time, levels."""
    with np.load(winter_file(dec_year)) as f:
        return {k: f[k] for k in f.files}


def make_wind(u, v, time, n_lon=240, n_lat=121):
    """Return wind(t, lat, lon) interpolating gridded u, v of shape (time, lon, lat).
    t is seconds since time[0] (scalar or one per balloon).
    Bilinear in space (4 surrounding grid points), linear in time (6-hourly snapshots).
    Grid: lon = 0, 1.5, ..., 358.5 and lat = -90, -88.5, ..., 90."""
    t_grid = (time - time[0]) / np.timedelta64(1, "s")
    dt_grid = t_grid[1] - t_grid[0]

    def bilinear(field, k, lat, lon):
        x = (lon % 360.0) / GRID_STEP                 # fractional index in longitude
        y = (lat + 90.0) / GRID_STEP                  # fractional index in latitude
        i0 = np.floor(x).astype(int); fx = x - i0
        j0 = np.clip(np.floor(y).astype(int), 0, n_lat - 2); fy = y - j0
        i0 = i0 % n_lon; i1 = (i0 + 1) % n_lon       # wrap round the globe
        return ((1 - fx) * (1 - fy) * field[k, i0, j0] + fx * (1 - fy) * field[k, i1, j0]
                + (1 - fx) * fy * field[k, i0, j0 + 1] + fx * fy * field[k, i1, j0 + 1])

    def wind(t, lat, lon):
        t = np.broadcast_to(t, np.shape(lat))
        k = np.minimum((t // dt_grid).astype(int), len(t_grid) - 2)   # snapshot before t
        a = (t - t_grid[k]) / dt_grid                                   # 0..1 between snapshots
        uu = (1 - a) * bilinear(u, k, lat, lon) + a * bilinear(u, k + 1, lat, lon)
        vv = (1 - a) * bilinear(v, k, lat, lon) + a * bilinear(v, k + 1, lat, lon)
        return uu, vv

    return wind


# ---------------------------------------------------------------- stations and the gap

STATION_URL = "https://www.ncei.noaa.gov/pub/data/igra/igra2-station-list.txt"

# Added by hand (decisions.md): IGRA2 omits Keflavik and shows Egilsstadir ending 2024,
# but AIP Iceland GEN 3.5 and ENR 5.3 say both still launch.
ICELAND_EXTRA = pd.DataFrame([
    dict(id="AIP-KEF", name="KEFLAVIK (AIP GEN 3.5)",    lat=63.97, lon=-22.60),
    dict(id="AIP-EGS", name="EGILSSTADIR (AIP ENR 5.3)", lat=65.28, lon=-14.40),
])


def active_stations(last_year=2026, add_iceland=True):
    """IGRA2 stations whose last year of data is >= last_year (plus Iceland, see above)."""
    path = DATA / "igra2-station-list.txt"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(STATION_URL, path)
    colspecs = [(0, 11), (12, 20), (21, 30), (31, 37), (41, 71), (72, 76), (77, 81), (82, 88)]
    names = ["id", "lat", "lon", "elev_m", "name", "first_year", "last_year", "n_obs"]
    st = pd.read_fwf(path, colspecs=colspecs, names=names)
    st = st[st.last_year >= last_year]
    if add_iceland:
        st = pd.concat([st[st.id != "ICM00004089"], ICELAND_EXTRA], ignore_index=True)
    return st


def region_grid(lon_max=GAP_LON_MAX):
    """Latitudes and longitudes of the gap region's grid cells (1.5 degree spacing).
    lon_max lets a sensitivity check widen the box east; the main result uses 30E."""
    lats = np.arange(GAP_LAT_MIN, GAP_LAT_MAX + 0.01, GRID_STEP)
    lons = np.arange(GAP_LON_MIN, lon_max + 0.01, GRID_STEP)
    return lats, lons


def nearest_station_km_grid(stations, lon_max=GAP_LON_MAX):
    """Distance (km) from each region grid cell to its nearest station, shape (n_lat, n_lon)."""
    lats, lons = region_grid(lon_max)
    LAT, LON = np.meshgrid(lats, lons, indexing="ij")
    d = great_circle_km(LAT.ravel()[:, None], LON.ravel()[:, None],
                        stations.lat.values[None, :], stations.lon.values[None, :])
    return d.min(axis=1).reshape(LAT.shape)


def in_gap(lat, lon, gap_mask, lon_max=GAP_LON_MAX):
    """True where (lat, lon) falls in a gap cell. gap_mask is a boolean (n_lat, n_lon) grid
    over the region; each point is assigned to its nearest grid cell. Points outside the
    region, or NaN (stopped balloons), are never in the gap."""
    lats, lons = region_grid(lon_max)
    lat = np.asarray(lat); lon = np.asarray(lon)
    ok = (np.isfinite(lat) & (lat >= GAP_LAT_MIN - GRID_STEP / 2)
          & (lon >= GAP_LON_MIN - GRID_STEP / 2) & (lon <= lon_max + GRID_STEP / 2))
    i = np.clip(np.rint((np.nan_to_num(lat) - GAP_LAT_MIN) / GRID_STEP).astype(int), 0, len(lats) - 1)
    j = np.clip(np.rint((np.nan_to_num(lon) - GAP_LON_MIN) / GRID_STEP).astype(int), 0, len(lons) - 1)
    return ok & gap_mask[i, j]


# ---------------------------------------------------------------- one winter of launches

def fly_winter(winter, sites, level_index, hours=21 * 24, pole_safe=True):
    """Launch one balloon per site every day at 00 UTC, 1 Dec to end Feb, at one level.
    winter is the December year. Returns (lats, lons, site_names, launch_days), with
    lats/lons of shape (hours + 1, n_balloons)."""
    w = load_winter(winter)
    days = pd.date_range(f"{winter}-12-01", f"{winter + 1}-03-01", freq="D", inclusive="left")
    names = list(sites)
    site_idx = np.tile(np.arange(len(names)), len(days))
    day_idx = np.repeat(np.arange(len(days)), len(names))
    lat0 = np.array([sites[n][0] for n in names])[site_idx]
    lon0 = np.array([sites[n][1] for n in names])[site_idx]
    t0 = (days.values[day_idx] - w["time"][0]) / np.timedelta64(1, "s")
    wind = make_wind(w["u"][:, level_index], w["v"][:, level_index], w["time"])
    flyer = fly_xyz if pole_safe else fly
    _, lats, lons = flyer(wind, lat0, lon0, t0, hours=hours)
    return lats, lons, np.array(names)[site_idx], days.values[day_idx]


# ---------------------------------------------------------------- greedy steering

def distance_to_gap_km(lat, lon, gap_lats, gap_lons):
    """Distance (km) from each balloon to the nearest gap cell centre. NaN-safe."""
    d = great_circle_km(np.asarray(lat)[:, None], np.asarray(lon)[:, None],
                        gap_lats[None, :], gap_lons[None, :])
    return d.min(axis=1)


def frozen(wind, t_fixed):
    """A wind field stuck at time t_fixed: the 'persistence' forecast (weather stays as it is now)."""
    return lambda t, lat, lon: wind(t_fixed, lat, lon)


def fly_steered(winds, lat0, lon0, t0, hours, gap_mask, tiebreak="closest",
                start_level=1, decide_every_h=6, lon_max=GAP_LON_MAX, lookahead="perfect"):
    """Simple greedy steering (not WindBorne's autopilot, and not a strict bound).
    lookahead="perfect":     choose using the real winds of the next 6 hours (hindsight; optimistic)
    lookahead="persistence": choose using only the winds at the moment of decision, assumed
                             frozen for 6 hours; the balloon then flies the real winds (pessimistic)
    winds: list of wind functions, one per level (same order as LEVELS).
    Every decide_every_h hours, each balloon tries every level for the next block and picks
    the one that gives the most hours in the gap during that block. Ties:
      tiebreak="stay":    keep the current level (the brief's rule)
      tiebreak="closest": pick the level that ends the block closest to the gap
    Level changes are instant (a stated simplification).
    Returns (lats, lons, levels_used) with lats/lons of shape (hours + 1, n)."""
    lat = np.atleast_1d(np.asarray(lat0, dtype=float)).copy()
    lon = np.atleast_1d(np.asarray(lon0, dtype=float)).copy()
    t0 = np.broadcast_to(np.asarray(t0, dtype=float), lat.shape)
    n, n_lev = lat.size, len(winds)
    n_blocks = int(hours // decide_every_h)

    lats_r, lons_r = region_grid(lon_max)
    gi, gj = np.where(gap_mask)
    gap_lats, gap_lons = lats_r[gi], lons_r[gj]          # centres of gap cells

    lats = np.empty((n_blocks * decide_every_h + 1, n)); lons = np.empty_like(lats)
    lats[0], lons[0] = lat, lon
    level = np.full(n, start_level)
    levels_used = np.empty((n_blocks, n), dtype=int)

    for k in range(n_blocks):
        t_start = t0 + k * decide_every_h * 3600.0
        tries_lat, tries_lon, score, end_dist = [], [], [], []
        for L in range(n_lev):
            # the path the balloon would really fly at level L
            _, la, lo = fly_xyz(winds[L], lat, lon, t_start, hours=decide_every_h)
            tries_lat.append(la); tries_lon.append(lo)
            # the path the pilot *expects*, which is what the choice is based on
            if lookahead == "persistence":
                _, ela, elo = fly_xyz(frozen(winds[L], t_start), lat, lon, t_start, hours=decide_every_h)
            else:
                ela, elo = la, lo
            score.append(in_gap(ela[1:], elo[1:], gap_mask, lon_max).sum(axis=0))
            end_dist.append(distance_to_gap_km(ela[-1], elo[-1], gap_lats, gap_lons))
        score = np.array(score)                    # (n_lev, n)
        end_dist = np.array(end_dist)
        best = score.max(axis=0)
        tied = score == best                       # levels sharing the best score
        if tiebreak == "stay":
            choice = np.where(tied[level, np.arange(n)], level, score.argmax(axis=0))
        else:
            choice = np.where(tied, end_dist, np.inf).argmin(axis=0)
        level = choice
        levels_used[k] = choice
        sl = slice(k * decide_every_h + 1, (k + 1) * decide_every_h + 1)
        all_lat = np.array(tries_lat); all_lon = np.array(tries_lon)   # (n_lev, steps+1, n)
        lats[sl] = all_lat[choice, 1:, np.arange(n)].T
        lons[sl] = all_lon[choice, 1:, np.arange(n)].T
        lat, lon = lats[sl.stop - 1], lons[sl.stop - 1]
    return lats, lons, levels_used
