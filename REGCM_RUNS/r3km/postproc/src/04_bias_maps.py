"""
04_bias_maps.py
===============
Description: Calculates and plots 2D spatial bias maps (Model - Observation).
Author: M. El Aabaribaoune (@um6p)
"""

#!/usr/bin/env python3
"""
04_bias_maps.py  –  Model − Observation Bias Maps (Annual + Seasonal)
=====================================================================
Reads model-on-obs grid and obs files to compute and plot:
  • Annual mean bias map
  • Seasonal bias maps (DJF / MAM / JJA / SON)

Outputs → postproc/results/maps/
  bias_annual_<var>_<year>.png
  bias_seasonal_<var>_<year>.png

Usage:
    python3 src/04_bias_maps.py [--year 2000] [--vars pr,tasmax,tasmin]
"""

import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_parser import *

import netCDF4 as nc
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import TwoSlopeNorm
import warnings; warnings.filterwarnings("ignore")

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False

parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, default=YEAR_START)
parser.add_argument("--vars", default=",".join(VARIABLES))
args    = parser.parse_args()
YEAR    = args.year
varlist = [v.strip() for v in args.vars.split(",")]
MAPS_DIR.mkdir(parents=True, exist_ok=True)

print(f"\n{'═'*60}")
print(f"  04_bias_maps — year {YEAR}")
print(f"{'═'*60}")


def load_nc(fpath, var):
    with nc.Dataset(fpath) as ds:
        data = ds.variables[var][:]
        t    = ds.variables["time"][:]
        t_units = ds.variables["time"].units
        if "xlat" in ds.variables:
            lat = ds.variables["xlat"][:]
            lon = ds.variables["xlon"][:]
            curvi = True
        elif "lat" in ds.variables:
            lat = ds.variables["lat"][:]
            lon = ds.variables["lon"][:]
            curvi = False
        else:
            raise KeyError("No lat/lon found")
    return data, lat, lon, t, t_units, curvi


def get_month_mask(t_arr, t_units, months):
    from netCDF4 import num2date
    dates = num2date(t_arr, t_units, calendar="standard")
    return np.array([d.month in months for d in dates])


def seasonal_mean(data, t, tunits, months):
    mask = get_month_mask(t, tunits, months)
    if mask.sum() == 0:
        return np.full(data.shape[1:], np.nan)
    return np.nanmean(data[mask], axis=0)


def add_features(ax):
    if HAS_CARTOPY:
        ax.add_feature(cfeature.COASTLINE, linewidth=0.6, color="k")
        ax.add_feature(cfeature.BORDERS,   linewidth=0.4, color="gray")
        gl = ax.gridlines(draw_labels=True, linewidth=0.3,
                          color="gray", alpha=0.5, linestyle="--")
        gl.top_labels = False; gl.right_labels = False
        gl.xlocator = mticker.MultipleLocator(5)
        gl.ylocator = mticker.MultipleLocator(5)


def plot_bias_panel(ax, lon, lat, bias, norm, cmap, title, curvi=False):
    if HAS_CARTOPY:
        if curvi:
            pc = ax.pcolormesh(lon, lat, bias, cmap=cmap, norm=norm,
                               transform=ccrs.PlateCarree(), shading="auto")
        else:
            lo2, la2 = np.meshgrid(lon, lat)
            pc = ax.pcolormesh(lo2, la2, bias, cmap=cmap, norm=norm,
                               transform=ccrs.PlateCarree(), shading="auto")
        add_features(ax)
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()],
                      crs=ccrs.PlateCarree())
    else:
        if curvi:
            pc = ax.pcolormesh(lon, lat, bias, cmap=cmap, norm=norm, shading="auto")
        else:
            lo2, la2 = np.meshgrid(lon, lat)
            pc = ax.pcolormesh(lo2, la2, bias, cmap=cmap, norm=norm, shading="auto")
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title(title, fontsize=9, fontweight="bold")
    return pc


def bias_norm_cmap(var, vcap=None):
    cfg  = MODEL[var]
    vmax = vcap if vcap else cfg["bias_vmax"]
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    cmap = plt.get_cmap(cfg["cmap_bias"])
    return norm, cmap, vmax


def process_var(var, year):
    # model is on obs grid (coarse) for fair comparison
    mod_f = DATA_DIR / f"model_{var}_on_obs_{year}.nc"
    obs_f = DATA_DIR / f"obs_{var}_{year}.nc"

    if not mod_f.exists() or not obs_f.exists():
        print(f"  ⚠  {var}: intermediate files missing — run 01 + 02 first")
        return

    mod, mlat, mlon, mt, mtu, mc = load_nc(mod_f, var)
    obs, olat, olon, ot, otu, oc = load_nc(obs_f, var)

    # Align shapes (should match since mod is on obs grid)
    if mod.shape != obs.shape:
        print(f"  ⚠  {var}: shape mismatch mod={mod.shape} obs={obs.shape}")
        nmin = min(mod.shape[0], obs.shape[0])
        mod = mod[:nmin]; obs = obs[:nmin]; mt = mt[:nmin]

    cfg  = MODEL[var]
    unit = cfg["units_out"]
    norm, cmap, vmax = bias_norm_cmap(var)

    # ── A) Annual bias ────────────────────────────────────────────────────────
    mod_ann = np.nanmean(mod, axis=0)
    obs_ann = np.nanmean(obs, axis=0)
    bias_ann = mod_ann - obs_ann

    if HAS_CARTOPY:
        proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(1, 1, figsize=(9, 7),
                               subplot_kw={"projection": proj})
    else:
        fig, ax = plt.subplots(figsize=(9, 7))

    pc = plot_bias_panel(ax, mlon, mlat, bias_ann, norm, cmap,
                         f"Annual Bias  [{cfg['long_name']}] — RegCM − {OBS[var]['label']}",
                         curvi=mc)
    cbar = fig.colorbar(pc, ax=ax, shrink=0.7, pad=0.04)
    cbar.set_label(f"Bias ({unit})", fontsize=10)
    fig.suptitle(f"Annual Mean Bias  —  {var}  —  {year}",
                 fontsize=12, fontweight="bold")
    out = MAPS_DIR / f"bias_annual_{var}_{year}.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✔ {out.name}")

    # ── B) Seasonal bias 2×2 ─────────────────────────────────────────────────
    season_names = list(SEASONS.keys())
    if HAS_CARTOPY:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10),
                                 subplot_kw={"projection": proj})
    else:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.ravel()

    for i, sname in enumerate(season_names):
        months = SEASONS[sname]
        sm = seasonal_mean(mod, mt, mtu, months)
        so = seasonal_mean(obs, mt, mtu, months)
        bias_s = sm - so
        title = f"{sname}  Bias  RegCM − {OBS[var]['label']}"
        pc = plot_bias_panel(axes[i], mlon, mlat, bias_s, norm, cmap, title, curvi=mc)

    cbar = fig.colorbar(pc, ax=axes.tolist(), shrink=0.6,
                        orientation="horizontal", pad=0.05)
    cbar.set_label(f"Bias ({unit})", fontsize=10)
    fig.suptitle(f"Seasonal Bias  —  {var}  —  {year}",
                 fontsize=12, fontweight="bold")
    out = MAPS_DIR / f"bias_seasonal_{var}_{year}.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✔ {out.name}")


for var in varlist:
    print(f"\n  ── {var} ──────────────────────")
    process_var(var, YEAR)

print(f"\n{'═'*60}")
print(f"  ✔  Bias maps done — {MAPS_DIR}")
print(f"{'═'*60}\n")
