"""
05_seasonal_cycle.py
====================
Description: Computes and visualizes the seasonal cycle (time series) over the specified domain.
Author: M. El Aabaribaoune (@um6p)
"""

#!/usr/bin/env python3
"""
05_seasonal_cycle.py  –  Area-Averaged Monthly/Seasonal Cycle
=============================================================
Computes area-average over the Morocco domain bbox (config.py)
and plots monthly mean climatology: Model vs Observation.

Output → postproc/results/timeseries/
  seasonal_cycle_<var>_<year>.png

Usage:
    python3 src/05_seasonal_cycle.py [--year 2000] [--vars pr,tasmax,tasmin]
"""

import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_parser import *

import netCDF4 as nc
from netCDF4 import num2date
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import warnings; warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, default=YEAR_START)
parser.add_argument("--vars", default=",".join(VARIABLES))
args    = parser.parse_args()
YEAR    = args.year
varlist = [v.strip() for v in args.vars.split(",")]
TS_DIR.mkdir(parents=True, exist_ok=True)

print(f"\n{'═'*60}")
print(f"  05_seasonal_cycle — year {YEAR}")
print(f"{'═'*60}")

MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]

COLORS = {
    "model": "#E63946",    # vivid red
    "obs"  : "#457B9D",    # steel blue
}


def load_nc(fpath, var):
    with nc.Dataset(fpath) as ds:
        data = ds.variables[var][:]
        t    = ds.variables["time"][:]
        t_units = ds.variables["time"].units
        if "xlat" in ds.variables:
            lat = ds.variables["xlat"][:]
            lon = ds.variables["xlon"][:]
            mask_var = ds.variables.get("mask", None)
            mask = mask_var[:] if mask_var is not None else None
        else:
            lat = ds.variables["lat"][:]
            lon = ds.variables["lon"][:]
            mask = None
    return data, lat, lon, t, t_units, mask


def bbox_mask(lat, lon, bbox):
    """Return boolean mask True where lat/lon inside bbox."""
    return ((lat >= bbox["lat_min"]) & (lat <= bbox["lat_max"]) &
            (lon >= bbox["lon_min"]) & (lon <= bbox["lon_max"]))


def area_average(data, lat, lon, bbox, land_mask=None):
    """
    Area-weighted mean over bbox for each time step.
    data: (ntime, ny, nx) or (ntime, nlat, nlon)
    Returns: (ntime,) array
    """
    spatial_mask = bbox_mask(lat, lon, bbox)   # (ny, nx) or (nlat, nlon)
    if land_mask is not None:
        spatial_mask = spatial_mask & (land_mask == 1)

    # cosine-latitude weights
    if lat.ndim == 2:
        weights = np.cos(np.deg2rad(lat))
    else:
        weights_1d = np.cos(np.deg2rad(lat))
        weights = np.tile(weights_1d[:, np.newaxis], (1, lon.shape[0]))

    weights = np.where(spatial_mask, weights, 0.0)
    total_w = weights.sum()
    if total_w == 0:
        return np.full(data.shape[0], np.nan)

    avgs = np.full(data.shape[0], np.nan)
    for i in range(data.shape[0]):
        field = data[i]
        if hasattr(field, "data"):
            field = np.where(field.mask, np.nan, field.data)
        valid = np.isfinite(field)
        w = np.where(valid & spatial_mask, weights, 0.0)
        wsum = w.sum()
        if wsum > 0:
            avgs[i] = np.nansum(field * w) / wsum
    return avgs


def monthly_mean_and_std(ts, t_arr, t_units):
    """Return monthly mean and std arrays (12,)."""
    dates = num2date(t_arr, t_units, calendar="standard")
    months_ts = np.array([d.month for d in dates])
    means = np.full(12, np.nan)
    stds  = np.full(12, np.nan)
    for m in range(1, 13):
        sel = ts[months_ts == m]
        sel = sel[np.isfinite(sel)]
        if len(sel) > 0:
            means[m-1] = sel.mean()
            stds[m-1]  = sel.std()
    return means, stds


def process_var(var, year):
    mod_f  = DATA_DIR / f"model_{var}_{year}.nc"
    obs_f  = DATA_DIR / f"obs_{var}_{year}.nc"

    if not mod_f.exists() or not obs_f.exists():
        print(f"  ⚠  {var}: files missing, run 01_preprocess first")
        return

    mod_data, mlat, mlon, mt, mtu, mmask = load_nc(mod_f, var)
    obs_data, olat, olon, ot, otu, _     = load_nc(obs_f, var)

    cfg  = MODEL[var]
    bbox = DOMAIN_BBOX

    # Area averages
    mod_ts = area_average(mod_data, mlat, mlon, bbox, land_mask=mmask)
    obs_ts = area_average(obs_data, olat, olon, bbox)

    # Monthly climatology
    mod_means, mod_stds = monthly_mean_and_std(mod_ts, mt, mtu)
    obs_means, obs_stds = monthly_mean_and_std(obs_ts, ot, otu)

    x = np.arange(1, 13)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#F8F9FA")
    ax.set_facecolor("#F8F9FA")

    # Shaded uncertainty band
    ax.fill_between(x, mod_means - mod_stds, mod_means + mod_stds,
                    alpha=0.15, color=COLORS["model"])
    ax.fill_between(x, obs_means - obs_stds, obs_means + obs_stds,
                    alpha=0.15, color=COLORS["obs"])

    # Lines
    ax.plot(x, mod_means, "o-", color=COLORS["model"], lw=2, ms=6,
            label=f"RegCM r3km", zorder=5)
    ax.plot(x, obs_means, "s--", color=COLORS["obs"],   lw=2, ms=6,
            label=f"{OBS[var]['label']}", zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel(f"{cfg['long_name']} ({cfg['units_out']})", fontsize=11)
    ax.set_title(
        f"Monthly Cycle  —  {cfg['long_name']}  —  Year {year}\n"
        f"Area average: lat [{bbox['lat_min']}–{bbox['lat_max']}°N], "
        f"lon [{bbox['lon_min']}–{bbox['lon_max']}°E]",
        fontsize=11, fontweight="bold"
    )
    ax.legend(fontsize=10, framealpha=0.8)
    ax.grid(axis="y", alpha=0.4, linestyle="--")
    ax.spines[["top", "right"]].set_visible(False)

    out = TS_DIR / f"seasonal_cycle_{var}_{year}.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✔ {out.name}")

    # Print quick table
    print(f"       {'Month':>5}  {'Model':>8}  {'Obs':>8}  {'Bias':>8}")
    for i, ml in enumerate(MONTH_LABELS):
        b = mod_means[i] - obs_means[i] if np.isfinite(mod_means[i]) and np.isfinite(obs_means[i]) else np.nan
        print(f"       {ml:>5}  {mod_means[i]:>8.2f}  {obs_means[i]:>8.2f}  {b:>8.2f}")


for var in varlist:
    print(f"\n  ── {var} ──────────────────────")
    process_var(var, YEAR)

print(f"\n{'═'*60}")
print(f"  ✔  Seasonal cycle plots done — {TS_DIR}")
print(f"{'═'*60}\n")
