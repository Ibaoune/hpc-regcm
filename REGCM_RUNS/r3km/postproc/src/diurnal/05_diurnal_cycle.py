#!/usr/bin/env python3
# ==============================================================================
# Script Name: 05_diurnal_cycle.py
# Description: Diurnal Cycle Comparison (RegCM vs ERA5 Subdaily)
# Author: M. El Aabaribaoune (@um6p)
# ==============================================================================
"""
05_diurnal_cycle.py
===================
Computes and visualizes the diurnal cycle of precipitation and 2m temperature:
1. Hourly mean diurnal curves (00h to 23h UTC) for Morocco across seasons:
   - Annual, DJF, MAM, JJA, SON
   - Peak hour timing, nadir hour timing, diurnal amplitude
2. Spatial maps across the Moroccan domain:
   - Peak hour (phase) of the diurnal cycle (RegCM, ERA5, Difference)
   - Diurnal amplitude (RegCM, ERA5, Bias)
3. Quantitative summary metrics exported to CSV.
"""

import os
import sys
import glob
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import netCDF4 as nc
from scipy.spatial import cKDTree
from matplotlib.path import Path as MplPath
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
from shapely.ops import unary_union
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import src.commun.config_parser as cp
from src.commun.core.plot_style import apply_publication_style, get_variable_units, get_nan_color
from src.commun.core.map_plotting import prepare_map_axis, HAS_CARTOPY

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

apply_publication_style()

SEASONS = ["Annual", "DJF", "MAM", "JJA", "SON"]

def get_morocco_geometry():
    """Retrieve full Morocco unified geometry (including Western Sahara)."""
    shpfilename = shpreader.natural_earth(resolution='50m', category='cultural', name='admin_0_countries')
    reader = shpreader.Reader(shpfilename)
    geoms = [c.geometry for c in reader.records() if c.attributes.get('NAME') in ['Morocco', 'Western Sahara', 'W. Sahara']]
    if not geoms:
        shpfilename = shpreader.natural_earth(resolution='110m', category='cultural', name='admin_0_countries')
        reader = shpreader.Reader(shpfilename)
        geoms = [c.geometry for c in reader.records() if c.attributes.get('NAME') in ['Morocco', 'Western Sahara', 'W. Sahara']]
    return unary_union(geoms)

def compute_polygon_mask(lon_2d, lat_2d, geometry):
    """Compute boolean 2D mask for points inside geometry."""
    pts = np.column_stack((lon_2d.ravel(), lat_2d.ravel()))
    mask = np.zeros(pts.shape[0], dtype=bool)
    polys = [geometry] if geometry.geom_type == 'Polygon' else geometry.geoms
    for poly in polys:
        ext = np.asarray(poly.exterior.coords)
        path = MplPath(ext)
        mask |= path.contains_points(pts)
        for interior in poly.interiors:
            path_in = MplPath(np.asarray(interior.coords))
            mask &= ~path_in.contains_points(pts)
    return mask.reshape(lon_2d.shape)

def get_cached_masks_and_grid(sample_regcm_file, sample_era5_file):
    """
    Computes/loads cached masks and spatial cropping bounding boxes.
    Returns:
      regcm_crop_info: (iy_min, iy_max, jx_min, jx_max, xlat_crop, xlon_crop, regcm_mask_crop)
      era5_crop_info:  (ilat_min, ilat_max, ilon_min, ilon_max, elat_crop, elon_crop, era5_mask_crop)
      tree_weights:    (indices, weights) for regridding RegCM crop to ERA5 crop
    """
    cache_dir = cp.DATA_DIR / "masks"
    cache_dir.mkdir(parents=True, exist_ok=True)
    geom = get_morocco_geometry()

    # 1. RegCM grid & mask
    with nc.Dataset(sample_regcm_file) as ds:
        xlat = ds.variables['xlat'][:]
        xlon = ds.variables['xlon'][:]

    regcm_mask_file = cache_dir / "morocco_regcm_mask.npy"
    if regcm_mask_file.exists():
        logger.info(f"Loading cached RegCM Morocco mask from {regcm_mask_file}")
        regcm_mask = np.load(regcm_mask_file)
    else:
        logger.info("Computing 2D spatial mask on full RegCM grid...")
        regcm_mask = compute_polygon_mask(xlon, xlat, geom)
        np.save(regcm_mask_file, regcm_mask)

    iy_indices, jx_indices = np.where(regcm_mask)
    buf = 10
    iy_min = max(0, iy_indices.min() - buf)
    iy_max = min(xlat.shape[0], iy_indices.max() + buf + 1)
    jx_min = max(0, jx_indices.min() - buf)
    jx_max = min(xlat.shape[1], jx_indices.max() + buf + 1)

    xlat_crop = xlat[iy_min:iy_max, jx_min:jx_max]
    xlon_crop = xlon[iy_min:iy_max, jx_min:jx_max]
    regcm_mask_crop = regcm_mask[iy_min:iy_max, jx_min:jx_max]

    regcm_crop_info = (iy_min, iy_max, jx_min, jx_max, xlat_crop, xlon_crop, regcm_mask_crop)

    # 2. ERA5 grid & mask
    with nc.Dataset(sample_era5_file) as ds:
        lats = ds.variables['latitude'][:]
        lons = ds.variables['longitude'][:]

    ilat = np.where((lats >= 20.0) & (lats <= 36.5))[0]
    ilon = np.where((lons >= -18.0) & (lons <= 0.0))[0]
    ilat_min, ilat_max = ilat.min(), ilat.max() + 1
    ilon_min, ilon_max = ilon.min(), ilon.max() + 1

    elat_crop = lats[ilat_min:ilat_max]
    elon_crop = lons[ilon_min:ilon_max]

    era5_mask_file = cache_dir / "morocco_era5_mask_crop.npy"
    if era5_mask_file.exists():
        logger.info(f"Loading cached ERA5 Morocco mask from {era5_mask_file}")
        era5_mask_crop = np.load(era5_mask_file)
    else:
        logger.info("Computing 2D spatial mask on cropped ERA5 grid...")
        elon2d, elat2d = np.meshgrid(elon_crop, elat_crop)
        era5_mask_crop = compute_polygon_mask(elon2d, elat2d, geom)
        np.save(era5_mask_file, era5_mask_crop)

    era5_crop_info = (ilat_min, ilat_max, ilon_min, ilon_max, elat_crop, elon_crop, era5_mask_crop)

    # 3. KDTree for Bilinear Interpolation (RegCM crop -> ERA5 crop)
    logger.info("Initializing KDTree weights for regridding...")
    elon2d, elat2d = np.meshgrid(elon_crop, elat_crop)
    era5_pts = np.column_stack((elon2d.ravel(), elat2d.ravel()))
    regcm_pts = np.column_stack((xlon_crop.ravel(), xlat_crop.ravel()))

    tree = cKDTree(regcm_pts)
    dists, indices = tree.query(era5_pts, k=4)
    weights = 1.0 / np.maximum(dists, 1e-6)
    weights /= weights.sum(axis=1, keepdims=True)
    tree_weights = (indices, weights, elat_crop.shape[0], elon_crop.shape[0])

    return regcm_crop_info, era5_crop_info, tree_weights

def get_seasons_dict():
    return {s: np.zeros(24, dtype=np.float64) for s in SEASONS}

def get_counts_dict():
    return {s: np.zeros(24, dtype=np.int64) for s in SEASONS}

def process_regcm(var_name, regcm_files, regcm_crop_info, start_date, end_date):
    """
    Extracts hourly diurnal curves and 2D diurnal cycles from RegCM files.
    """
    iy_min, iy_max, jx_min, jx_max, xlat_crop, xlon_crop, mask_crop = regcm_crop_info
    ny_c, nx_c = xlat_crop.shape

    hourly_mean_sum = get_seasons_dict()
    hourly_mean_cnt = get_counts_dict()

    hourly_grid_sum = {s: np.zeros((24, ny_c, nx_c), dtype=np.float64) for s in SEASONS}
    hourly_grid_cnt = {s: np.zeros(24, dtype=np.int64) for s in SEASONS}

    logger.info(f"Processing RegCM {var_name} across {len(regcm_files)} daily files...")

    # Determine scaling / offset
    # pr in SHF is kg m-2 s-1 -> multiply by 3600.0 for mm/h
    # tas in SRF is K -> subtract 273.15 for degC
    is_pr = (var_name == "pr")

    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    is_single_year = (start_dt.year == end_dt.year)

    for fpath in tqdm(regcm_files, desc=f"RegCM {var_name}"):
        with nc.Dataset(fpath) as ds:
            t_var = ds.variables['time']
            times = nc.num2date(t_var[:], t_var.units, calendar=getattr(t_var, 'calendar', 'standard'))

            if is_pr:
                # Shape (24, 917, 1081)
                vals = ds.variables['pr'][:, iy_min:iy_max, jx_min:jx_max] * 3600.0
            else:
                # Shape (24, 1, 917, 1081) or (24, 917, 1081)
                raw_tas = ds.variables['tas']
                if raw_tas.ndim == 4:
                    vals = raw_tas[:, 0, iy_min:iy_max, jx_min:jx_max] - 273.15
                else:
                    vals = raw_tas[:, iy_min:iy_max, jx_min:jx_max] - 273.15

        nt = len(times)
        for t_idx in range(nt):
            dt = pd.to_datetime(str(times[t_idx]))
            if dt < start_dt or dt > end_dt:
                continue

            h = dt.hour
            m = dt.month

            # Determine season (DJF: Dec, Jan, Feb)
            s_name = "DJF" if m in [1, 2, 12] else ("MAM" if m in [3, 4, 5] else ("JJA" if m in [6, 7, 8] else "SON"))

            slice_2d = vals[t_idx]

            # Regional mean over Morocco mask
            spatial_mean = np.nanmean(slice_2d[mask_crop])

            # Accumulate Annual
            hourly_mean_sum["Annual"][h] += spatial_mean
            hourly_mean_cnt["Annual"][h] += 1
            hourly_grid_sum["Annual"][h] += slice_2d
            hourly_grid_cnt["Annual"][h] += 1

            # Accumulate Season
            if s_name:
                hourly_mean_sum[s_name][h] += spatial_mean
                hourly_mean_cnt[s_name][h] += 1
                hourly_grid_sum[s_name][h] += slice_2d
                hourly_grid_cnt[s_name][h] += 1

    # Finalize means
    regcm_curves = {}
    regcm_grids = {}
    for s in SEASONS:
        c = np.maximum(hourly_mean_cnt[s], 1)
        regcm_curves[s] = hourly_mean_sum[s] / c

        gc = np.maximum(hourly_grid_cnt[s][:, None, None], 1)
        regcm_grids[s] = (hourly_grid_sum[s] / gc).astype(np.float32)

    return regcm_curves, regcm_grids

def process_era5(var_name, era5_files, era5_crop_info, start_date, end_date):
    """
    Extracts hourly diurnal curves and 2D diurnal cycles from ERA5 hourly file(s).
    """
    ilat_min, ilat_max, ilon_min, ilon_max, elat_crop, elon_crop, mask_crop = era5_crop_info
    ny_e, nx_e = elat_crop.shape[0], elon_crop.shape[0]

    hourly_mean_sum = get_seasons_dict()
    hourly_mean_cnt = get_counts_dict()

    hourly_grid_sum = {s: np.zeros((24, ny_e, nx_e), dtype=np.float64) for s in SEASONS}
    hourly_grid_cnt = {s: np.zeros(24, dtype=np.int64) for s in SEASONS}

    if isinstance(era5_files, (str, Path)):
        era5_files = [era5_files]

    era5_var = "tp" if var_name == "pr" else "t2m"
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    for era5_file in era5_files:
        logger.info(f"Processing ERA5 {era5_var} from {Path(era5_file).name}...")
        with nc.Dataset(era5_file) as ds:
            t_var = ds.variables['time']
            times = nc.num2date(t_var[:], t_var.units, calendar=getattr(t_var, 'calendar', 'standard'))

            logger.info("Reading cropped ERA5 block from disk...")
            if var_name == "pr":
                vals = ds.variables['tp'][:, ilat_min:ilat_max, ilon_min:ilon_max] * 1000.0 # m to mm/h
            else:
                vals = ds.variables['t2m'][:, ilat_min:ilat_max, ilon_min:ilon_max] - 273.15 # K to degC

        nt = len(times)
        logger.info(f"Accumulating ERA5 hourly slices (N={nt})...")
        for t_idx in range(nt):
            dt = pd.to_datetime(str(times[t_idx]))
            if dt < start_dt or dt > end_dt:
                continue

            h = dt.hour
            m = dt.month
            s_name = "DJF" if m in [1, 2, 12] else ("MAM" if m in [3, 4, 5] else ("JJA" if m in [6, 7, 8] else "SON"))

            slice_2d = vals[t_idx]
            spatial_mean = np.nanmean(slice_2d[mask_crop])

            # Accumulate Annual
            hourly_mean_sum["Annual"][h] += spatial_mean
            hourly_mean_cnt["Annual"][h] += 1
            hourly_grid_sum["Annual"][h] += slice_2d
            hourly_grid_cnt["Annual"][h] += 1

            # Accumulate Season
            if s_name:
                hourly_mean_sum[s_name][h] += spatial_mean
                hourly_mean_cnt[s_name][h] += 1
                hourly_grid_sum[s_name][h] += slice_2d
                hourly_grid_cnt[s_name][h] += 1

    era5_curves = {}
    era5_grids = {}
    for s in SEASONS:
        c = np.maximum(hourly_mean_cnt[s], 1)
        era5_curves[s] = hourly_mean_sum[s] / c

        gc = np.maximum(hourly_grid_cnt[s][:, None, None], 1)
        era5_grids[s] = (hourly_grid_sum[s] / gc).astype(np.float32)

    return era5_curves, era5_grids

def regrid_regcm_to_era5(regcm_grid, tree_weights):
    """Regrid RegCM 24-hour diurnal cycle onto cropped ERA5 grid."""
    indices, weights, ny_e, nx_e = tree_weights
    flat = regcm_grid.reshape(24, -1)
    regridded = np.sum(flat[:, indices] * weights, axis=2).reshape(24, ny_e, nx_e)
    return regridded

def compute_metrics(var_name, regcm_curves, era5_curves):
    """Compute peak hour, nadir hour, amplitude, and daily means."""
    metrics_list = []
    for s in SEASONS:
        rc = regcm_curves[s]
        ec = era5_curves[s]

        rc_peak_h = int(np.argmax(rc))
        rc_peak_v = float(rc[rc_peak_h])
        rc_min_h = int(np.argmin(rc))
        rc_min_v = float(rc[rc_min_h])
        rc_amp = rc_peak_v - rc_min_v
        rc_mean = float(np.mean(rc))

        ec_peak_h = int(np.argmax(ec))
        ec_peak_v = float(ec[ec_peak_h])
        ec_min_h = int(np.argmin(ec))
        ec_min_v = float(ec[ec_min_h])
        ec_amp = ec_peak_v - ec_min_v
        ec_mean = float(np.mean(ec))

        phase_diff = (rc_peak_h - ec_peak_h + 12) % 24 - 12
        amp_bias = rc_amp - ec_amp
        daily_bias = rc_mean - ec_mean

        metrics_list.append({
            "variable": var_name,
            "season": s,
            "model_peak_hour_utc": rc_peak_h,
            "model_peak_val": rc_peak_v,
            "era5_peak_hour_utc": ec_peak_h,
            "era5_peak_val": ec_peak_v,
            "phase_diff_hours": phase_diff,
            "model_amplitude": rc_amp,
            "era5_amplitude": ec_amp,
            "amplitude_bias": amp_bias,
            "model_daily_mean": rc_mean,
            "era5_daily_mean": ec_mean,
            "daily_mean_bias": daily_bias
        })
    return metrics_list

def plot_diurnal_curves(var_name, regcm_curves, era5_curves, metrics_list, out_png, year_str):
    """
    Renders 5-panel publication-grade diurnal cycle curve figures.
    """
    fig, axes = plt.subplots(1, 5, figsize=(20, 4.5), sharey=True)
    unit_str = "mm/h" if var_name == "pr" else "°C"
    var_label = "Precipitation" if var_name == "pr" else "2m Temperature"

    hours = np.arange(24)

    metrics_by_season = {m["season"]: m for m in metrics_list}

    for idx, s in enumerate(SEASONS):
        ax = axes[idx]
        rc = regcm_curves[s]
        ec = era5_curves[s]
        m = metrics_by_season[s]

        # RegCM curve
        ax.plot(hours, rc, color="#D95F02", lw=2.5, marker="o", markersize=4, label="RegCM (3km)")
        # ERA5 curve
        ax.plot(hours, ec, color="#1F78B4", lw=2.2, linestyle="--", marker="s", markersize=3.5, label="ERA5")

        ax.set_title(f"{s}", fontsize=13, fontweight='bold', pad=8)
        ax.set_xticks([0, 4, 8, 12, 16, 20])
        ax.set_xlim(0, 23)
        ax.grid(True, linestyle=":", alpha=0.6)

        if idx == 0:
            ax.set_ylabel(f"{var_label} ({unit_str})", fontsize=12, fontweight='bold')
            ax.legend(loc="upper left", frameon=True, fontsize=10)

        # Annotate peak timing and amplitude
        phase_sign = "+" if m["phase_diff_hours"] > 0 else ""
        annotation_txt = (
            f"Peak Mod: {m['model_peak_hour_utc']:02d}h UTC\n"
            f"Peak ERA5: {m['era5_peak_hour_utc']:02d}h UTC\n"
            f"Δt: {phase_sign}{m['phase_diff_hours']}h | Amp Bias: {m['amplitude_bias']:+.2f}"
        )
        ax.text(0.96, 0.04, annotation_txt, transform=ax.transAxes,
                fontsize=8.5, va="bottom", ha="right",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85, edgecolor="#ccc"))

    fig.text(0.5, 0.01, "Hour of Day (UTC)", ha="center", fontsize=12, fontweight="bold")
    fig.suptitle(f"Diurnal Cycle of {var_label} across Morocco — {year_str}", fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"✔ Saved diurnal curves figure: {out_png}")

def plot_spatial_maps(var_name, regcm_grid_rg, era5_grid, elon, elat, era5_mask, out_dir, year_str):
    """
    Renders 1x3 spatial maps of:
    1. Peak Hour (ERA5, RegCM, Phase Diff)
    2. Diurnal Amplitude (ERA5, RegCM, Bias)
    """
    extent = [-18.0, 0.0, 20.0, 36.5]
    unit_str = "mm/h" if var_name == "pr" else "°C"
    var_label = "Precipitation" if var_name == "pr" else "2m Temperature"

    elon2d, elat2d = np.meshgrid(elon, elat)

    for s in ["Annual", "JJA", "DJF"]:
        rc_2d = regcm_grid_rg[s]
        ec_2d = era5_grid[s]

        # 1. Peak Hour
        rc_peak = np.argmax(rc_2d, axis=0).astype(float)
        ec_peak = np.argmax(ec_2d, axis=0).astype(float)
        diff_peak = (rc_peak - ec_peak + 12) % 24 - 12

        # Mask outside Morocco
        rc_peak[~era5_mask] = np.nan
        ec_peak[~era5_mask] = np.nan
        diff_peak[~era5_mask] = np.nan

        fig, axes = plt.subplots(1, 3, figsize=(16, 5), subplot_kw={"projection": ccrs.PlateCarree()} if HAS_CARTOPY else None)
        for ax in axes:
            prepare_map_axis(ax, extent, cp.cfg.get("plotting", {}))
            ax.set_facecolor(get_nan_color())

        cmap_phase = plt.get_cmap("twilight_shifted")
        norm_phase = mcolors.Normalize(vmin=0, vmax=24)

        cmap_diff = plt.get_cmap("coolwarm")
        norm_diff = mcolors.Normalize(vmin=-6, vmax=6)

        p1 = axes[0].pcolormesh(elon2d, elat2d, ec_peak, cmap=cmap_phase, norm=norm_phase, shading="auto")
        axes[0].set_title(f"(a) ERA5 Peak Hour ({s})", fontweight="bold")

        p2 = axes[1].pcolormesh(elon2d, elat2d, rc_peak, cmap=cmap_phase, norm=norm_phase, shading="auto")
        axes[1].set_title(f"(b) RegCM Peak Hour ({s})", fontweight="bold")

        p3 = axes[2].pcolormesh(elon2d, elat2d, diff_peak, cmap=cmap_diff, norm=norm_diff, shading="auto")
        axes[2].set_title(f"(c) Phase Difference (RegCM − ERA5)", fontweight="bold")

        cbar1 = fig.colorbar(p1, ax=axes[:2].tolist(), orientation="vertical", shrink=0.75, ticks=[0, 4, 8, 12, 16, 20, 24])
        cbar1.set_label("Peak Hour (UTC)")

        cbar2 = fig.colorbar(p3, ax=axes[2], orientation="vertical", shrink=0.75, ticks=[-6, -4, -2, 0, 2, 4, 6])
        cbar2.set_label("Δ Hour (Mod − Obs)")

        fig.suptitle(f"{s} Peak Hour of {var_label} — {year_str}", fontsize=14, fontweight="bold", y=1.02)
        out_peak_png = out_dir / f"{var_name}_diurnal_peak_hour_{s.lower()}_{year_str}.png"
        fig.savefig(out_peak_png, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"✔ Saved peak hour map: {out_peak_png}")

        # 2. Diurnal Amplitude
        rc_amp = np.max(rc_2d, axis=0) - np.min(rc_2d, axis=0)
        ec_amp = np.max(ec_2d, axis=0) - np.min(ec_2d, axis=0)
        bias_amp = rc_amp - ec_amp

        rc_amp[~era5_mask] = np.nan
        ec_amp[~era5_mask] = np.nan
        bias_amp[~era5_mask] = np.nan

        fig, axes = plt.subplots(1, 3, figsize=(16, 5), subplot_kw={"projection": ccrs.PlateCarree()} if HAS_CARTOPY else None)
        for ax in axes:
            prepare_map_axis(ax, extent, cp.cfg.get("plotting", {}))
            ax.set_facecolor(get_nan_color())

        vmax_amp = float(np.nanpercentile(ec_amp, 98)) if np.sum(np.isfinite(ec_amp)) > 0 else 5.0
        vmax_amp = max(vmax_amp, 1.0 if var_name == "pr" else 10.0)

        cmap_amp = plt.get_cmap("YlGnBu" if var_name == "pr" else "OrRd")
        norm_amp = mcolors.Normalize(vmin=0, vmax=vmax_amp)

        max_bias = float(np.nanpercentile(np.abs(bias_amp), 98)) if np.sum(np.isfinite(bias_amp)) > 0 else 2.0
        max_bias = max(max_bias, 0.5 if var_name == "pr" else 3.0)

        cmap_bias = plt.get_cmap("BrBG" if var_name == "pr" else "RdBu_r")
        norm_bias = mcolors.Normalize(vmin=-max_bias, vmax=max_bias)

        p1 = axes[0].pcolormesh(elon2d, elat2d, ec_amp, cmap=cmap_amp, norm=norm_amp, shading="auto")
        axes[0].set_title(f"(a) ERA5 Amplitude ({s})", fontweight="bold")

        p2 = axes[1].pcolormesh(elon2d, elat2d, rc_amp, cmap=cmap_amp, norm=norm_amp, shading="auto")
        axes[1].set_title(f"(b) RegCM Amplitude ({s})", fontweight="bold")

        p3 = axes[2].pcolormesh(elon2d, elat2d, bias_amp, cmap=cmap_bias, norm=norm_bias, shading="auto")
        axes[2].set_title(f"(c) Amplitude Bias (RegCM − ERA5)", fontweight="bold")

        cbar1 = fig.colorbar(p1, ax=axes[:2].tolist(), orientation="vertical", shrink=0.75)
        cbar1.set_label(f"Diurnal Amplitude ({unit_str})")

        cbar2 = fig.colorbar(p3, ax=axes[2], orientation="vertical", shrink=0.75)
        cbar2.set_label(f"Amplitude Bias ({unit_str})")

        fig.suptitle(f"{s} Diurnal Amplitude of {var_label} — {year_str}", fontsize=14, fontweight="bold", y=1.02)
        out_amp_png = out_dir / f"{var_name}_diurnal_amplitude_{s.lower()}_{year_str}.png"
        fig.savefig(out_amp_png, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"✔ Saved amplitude map: {out_amp_png}")

def save_metrics_csv(all_metrics, out_csv):
    """Saves metrics to CSV file."""
    keys = [
        "variable", "season", "model_peak_hour_utc", "model_peak_val",
        "era5_peak_hour_utc", "era5_peak_val", "phase_diff_hours",
        "model_amplitude", "era5_amplitude", "amplitude_bias",
        "model_daily_mean", "era5_daily_mean", "daily_mean_bias"
    ]
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for m in all_metrics:
            writer.writerow({
                "variable": m["variable"],
                "season": m["season"],
                "model_peak_hour_utc": m["model_peak_hour_utc"],
                "model_peak_val": f"{m['model_peak_val']:.4f}",
                "era5_peak_hour_utc": m["era5_peak_hour_utc"],
                "era5_peak_val": f"{m['era5_peak_val']:.4f}",
                "phase_diff_hours": m["phase_diff_hours"],
                "model_amplitude": f"{m['model_amplitude']:.4f}",
                "era5_amplitude": f"{m['era5_amplitude']:.4f}",
                "amplitude_bias": f"{m['amplitude_bias']:.4f}",
                "model_daily_mean": f"{m['model_daily_mean']:.4f}",
                "era5_daily_mean": f"{m['era5_daily_mean']:.4f}",
                "daily_mean_bias": f"{m['daily_mean_bias']:.4f}"
            })
    logger.info(f"✔ Saved metrics table: {out_csv}")

def main():
    parser = argparse.ArgumentParser(description="Diurnal Cycle Evaluation: RegCM vs ERA5 Subdaily")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--vars", default="pr,tas", help="Comma-separated variables (e.g. pr,tas)")
    args = parser.parse_args()

    start_dt = pd.to_datetime(args.start_date)
    end_dt = pd.to_datetime(args.end_date)
    years = list(range(start_dt.year, end_dt.year + 1))
    year_str = str(start_dt.year) if start_dt.year == end_dt.year else f"{start_dt.year}-{end_dt.year}"
    period_str = f"{args.start_date}_to_{args.end_date}"

    logger.info(f"════════════════════════════════════════════════════════════")
    logger.info(f"  05_diurnal_cycle — Period: {period_str}")
    logger.info(f"════════════════════════════════════════════════════════════")

    out_diurnal_dir = cp.POSTPROC_ROOT / "results" / period_str / "diurnal"
    out_diurnal_dir.mkdir(parents=True, exist_ok=True)
    out_metrics_dir = cp.POSTPROC_ROOT / "results" / period_str / "metrics"
    out_metrics_dir.mkdir(parents=True, exist_ok=True)

    var_list = [v.strip() for v in args.vars.split(",")]

    era5_dir = Path("/home/mohammad.elaabaribao/lustre/climat-um6p-st-iwri-7ksifkvwkuy/shared/TEAM/data/ERA5/from_khadija/hourly")
    regcm_out_dir = cp.POSTPROC_ROOT.parent / cp.SIM_NAME / "output"

    all_era5_files = []
    all_regcm_shf = []
    all_regcm_srf = []

    for y in years:
        ef = era5_dir / f"era5_{y}.nc"
        if ef.exists():
            all_era5_files.append(str(ef))
        else:
            logger.warning(f"ERA5 file missing: {ef}")

        shf = sorted(glob.glob(str(regcm_out_dir / f"test_001_SHF.{y}*.nc")))
        srf = sorted(glob.glob(str(regcm_out_dir / f"test_001_SRF.{y}*.nc")))
        if not shf or not srf:
            archive_dir = cp.OUTPUT_DIR.parent / "archive_periods" / f"{y}_all"
            shf = sorted(glob.glob(str(archive_dir / f"test_001_SHF.{y}*.nc")))
            srf = sorted(glob.glob(str(archive_dir / f"test_001_SRF.{y}*.nc")))
        all_regcm_shf.extend(shf)
        all_regcm_srf.extend(srf)

    if not all_era5_files or not all_regcm_srf:
        logger.error(f"Missing ERA5 or RegCM input files for {period_str}")
        return

    # Setup masks and KDTree
    regcm_crop_info, era5_crop_info, tree_weights = get_cached_masks_and_grid(all_regcm_srf[0], all_era5_files[0])
    _, _, _, _, elat_crop, elon_crop, era5_mask = era5_crop_info

    all_metrics = []

    for v in var_list:
        logger.info(f"
─── Evaluating Diurnal Cycle for {v} across {len(years)} years ({period_str}) ───")
        regcm_files = all_regcm_shf if v == "pr" else all_regcm_srf

        # 1. RegCM
        regcm_curves, regcm_grids = process_regcm(v, regcm_files, regcm_crop_info, args.start_date, args.end_date)

        # 2. ERA5
        era5_curves, era5_grids = process_era5(v, all_era5_files, era5_crop_info, args.start_date, args.end_date)

        # 3. Metrics
        metrics = compute_metrics(v, regcm_curves, era5_curves)
        all_metrics.extend(metrics)

        # 4. Diurnal Curves Plot
        out_curve_png = out_diurnal_dir / f"{v}_diurnal_cycle_curves_{year_str}.png"
        plot_diurnal_curves(v, regcm_curves, era5_curves, metrics, out_curve_png, year_str)

        # 5. Regrid RegCM 2D to ERA5 and generate spatial maps
        logger.info(f"Regridding RegCM 2D diurnal cycles to ERA5 grid for spatial maps...")
        regcm_grids_rg = {}
        for s in SEASONS:
            regcm_grids_rg[s] = regrid_regcm_to_era5(regcm_grids[s], tree_weights)

        plot_spatial_maps(v, regcm_grids_rg, era5_grids, elon_crop, elat_crop, era5_mask, out_diurnal_dir, year_str)

    # Save Metrics CSV
    out_csv = out_metrics_dir / f"diurnal_cycle_metrics_{year_str}.csv"
    save_metrics_csv(all_metrics, out_csv)

    logger.info(f"
{'═'*60}")
    logger.info(f"  Figures: {out_diurnal_dir}")
    logger.info(f"  Metrics: {out_metrics_dir}")
    logger.info(f"{'═'*60}
")

if __name__ == "__main__":
    main()
