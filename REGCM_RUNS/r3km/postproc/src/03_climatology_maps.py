#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
"""
03_climatology_maps.py
======================
Generates integrated climatology evaluation figures (Observation, Model, Bias)
for each reference dataset. Supports Annual (1x3) and Seasonal (3x4) layouts.
Uses centralized src.core.map_plotting for geographic rendering and QA.
"""

import sys, os, argparse
import netCDF4 as nc
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.config_parser as cp
from src.core.map_plotting import (
    get_geographic_extent, prepare_map_axis, plot_qa_check,
    get_colormap_norm, save_figure_with_metadata, HAS_CARTOPY
)
import cartopy.crs as ccrs

def load_data(fpath, var):
    with nc.Dataset(fpath) as ds:
        data = ds.variables[var][:]
        t = ds.variables["time"][:]
        t_units = ds.variables["time"].units
        lat = ds.variables["lat"][:] if "lat" in ds.variables else ds.variables["xlat"][:]
        lon = ds.variables["lon"][:] if "lon" in ds.variables else ds.variables["xlon"][:]
    return data, lat, lon, t, t_units

def get_season_mask(t_arr, t_units, months):
    from netCDF4 import num2date
    dates = num2date(t_arr, t_units, calendar="standard")
    mask = np.array([d.month in months for d in dates])
    return mask

def process_evaluation(var, year, is_partial=False):
    cfg = cp.MODEL[var]
    unit = cfg["units_out"]
    
    for ref_name, obs_cfg in cp.OBS[var].items():
        if obs_cfg.get("type") == "stations": continue
        
        mod_native = cp.DATA_DIR / "processed" / "model" / var / f"{year}.nc"
        obs_native = cp.DATA_DIR / "processed" / "obs" / ref_name / var / f"{year}.nc"
        mod_on_obs = cp.DATA_DIR / "regridded" / ref_name / "model" / var / f"{year}.nc"
        
        if not mod_native.exists() or not obs_native.exists() or not mod_on_obs.exists():
            print(f"  ⚠  skipping {var} vs {ref_name}: files missing")
            continue
            
        m_nat_data, m_nat_lat, m_nat_lon, m_t, m_tu = load_data(mod_native, var)
        o_nat_data, o_nat_lat, o_nat_lon, o_t, o_tu = load_data(obs_native, var)
        m_rg_data, o_rg_lat, o_rg_lon, _, _ = load_data(mod_on_obs, var)
        
        # Determine extent
        extent = get_geographic_extent(m_nat_lon, m_nat_lat, o_nat_lon, o_nat_lat)
        if extent is None:
            print(f"  ⚠  Failed to determine valid extent for {var} vs {ref_name}. Skipping.")
            continue

        # Color configurations
        cmap_val, norm_val, levels_val, ext_val = get_colormap_norm(var, False, cp.cfg.get("plotting", {}))
        cmap_bias, norm_bias, levels_bias, ext_bias = get_colormap_norm(var, True, cp.cfg.get("plotting", {}))

        # ---------------------------------------------------------
        # ANNUAL FIGURE (1x3)
        # ---------------------------------------------------------
        m_ann = np.nanmean(m_nat_data, axis=0)
        o_ann = np.nanmean(o_nat_data, axis=0)
        m_rg_ann = np.nanmean(m_rg_data, axis=0)
        bias_ann = m_rg_ann - o_ann
        
        if is_partial:
            title_prefix = f"Partial Period Analysis ({year})"
        else:
            title_prefix = f"Annual Mean ({year})"
            
        try:
            plot_qa_check(f"{var}_{ref_name}_{year}", var, o_ann, o_nat_lon, o_nat_lat, ref_name, "Annual")
            plot_qa_check(f"{var}_RegCM_{year}", var, m_ann, m_nat_lon, m_nat_lat, "RegCM", "Annual")
        except ValueError as e:
            print(e)
            continue
            
        fig_ann, axes = plt.subplots(1, 3, figsize=(20, 6), subplot_kw={"projection": ccrs.PlateCarree()} if HAS_CARTOPY else None)
        axes = np.atleast_1d(axes)
        
        for ax in axes:
            prepare_map_axis(ax, extent, cp.cfg.get("plotting", {}))
            
        # OBS
        if o_nat_lon.ndim == 1:
            o_lon_m, o_lat_m = np.meshgrid(o_nat_lon, o_nat_lat)
        else:
            o_lon_m, o_lat_m = o_nat_lon, o_nat_lat
            
        pc1 = axes[0].pcolormesh(o_lon_m, o_lat_m, o_ann, cmap=cmap_val, norm=norm_val, shading="auto", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)
        axes[0].set_title(f"(a) {ref_name}")
        
        # MODEL
        pc2 = axes[1].pcolormesh(m_nat_lon, m_nat_lat, m_ann, cmap=cmap_val, norm=norm_val, shading="auto", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)
        axes[1].set_title(f"(b) RegCM")
        
        # BIAS
        if o_rg_lon.ndim == 1:
            rg_lon_m, rg_lat_m = np.meshgrid(o_rg_lon, o_rg_lat)
        else:
            rg_lon_m, rg_lat_m = o_rg_lon, o_rg_lat
            
        pc3 = axes[2].pcolormesh(rg_lon_m, rg_lat_m, bias_ann, cmap=cmap_bias, norm=norm_bias, shading="auto", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)
        axes[2].set_title(f"(c) Bias (RegCM - {ref_name})")
        
        fig_ann.colorbar(pc1, ax=axes[:2].tolist(), orientation="horizontal", shrink=0.7, pad=0.08, label=f"{unit}", extend=ext_val)
        fig_ann.colorbar(pc3, ax=axes[2], orientation="horizontal", shrink=0.7, pad=0.08, label=f"Bias ({unit})", extend=ext_bias)
        fig_ann.suptitle(f"{title_prefix} — {var.upper()} — RegCM vs {ref_name}", fontsize=16)
        
        out_ann = cp.MAPS_DIR / f"{var}_{ref_name}_annual_{year}.png"
        meta = {
            "config_hash": cp.get_config_hash(),
            "variable": var,
            "reference": ref_name,
            "statistic": "annual_mean" if not is_partial else "partial_mean",
            "extent": extent
        }
        save_figure_with_metadata(fig_ann, out_ann, meta)
        print(f"  ✔ {out_ann.name}")

        # ---------------------------------------------------------
        # SEASONAL FIGURE (3x4)
        # ---------------------------------------------------------
        seasons = ["MAM", "JJA", "SON", "DJF"]
        # Only evaluate complete seasons. For year 2001, assuming standard months
        # If partial, some seasons might be empty.
        
        # We will attempt to plot all 4, but if a season is empty, it fails QA.
        # Let's collect valid seasons
        season_data = {}
        for s in seasons:
            months = cp.SEASONS[s]
            m_mask = get_season_mask(m_t, m_tu, months)
            o_mask = get_season_mask(o_t, o_tu, months)
            
            if m_mask.sum() == 0 or o_mask.sum() == 0:
                print(f"  ⚠  Season {s} {year} is incomplete/missing. Skipping season.")
                continue
                
            m_s = np.nanmean(m_nat_data[m_mask], axis=0)
            o_s = np.nanmean(o_nat_data[o_mask], axis=0)
            m_rg_s = np.nanmean(m_rg_data[m_mask], axis=0)
            bias_s = m_rg_s - o_s
            
            season_data[s] = (o_s, m_s, bias_s)
            
        if not season_data:
            print(f"  ⚠  No valid seasons found for {var} vs {ref_name}.")
            continue
            
        fig_sea, axes_sea = plt.subplots(3, 4, figsize=(24, 15), subplot_kw={"projection": ccrs.PlateCarree()} if HAS_CARTOPY else None)
        
        for row in axes_sea:
            for ax in row:
                ax.set_visible(False) # hide all initially
                prepare_map_axis(ax, extent, cp.cfg.get("plotting", {}))
                
        valid_pc_val = None
        valid_pc_bias = None
                
        for col_idx, s in enumerate(seasons):
            if s not in season_data:
                continue
                
            o_s, m_s, bias_s = season_data[s]
            
            axes_sea[0, col_idx].set_visible(True)
            axes_sea[1, col_idx].set_visible(True)
            axes_sea[2, col_idx].set_visible(True)
            
            axes_sea[0, col_idx].set_title(f"{ref_name} - {s} {year}")
            pc_val = axes_sea[0, col_idx].pcolormesh(o_lon_m, o_lat_m, o_s, cmap=cmap_val, norm=norm_val, shading="auto", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)
            valid_pc_val = pc_val
            
            axes_sea[1, col_idx].set_title(f"RegCM - {s} {year}")
            axes_sea[1, col_idx].pcolormesh(m_nat_lon, m_nat_lat, m_s, cmap=cmap_val, norm=norm_val, shading="auto", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)
            
            axes_sea[2, col_idx].set_title(f"Bias - {s} {year}")
            pc_bias = axes_sea[2, col_idx].pcolormesh(rg_lon_m, rg_lat_m, bias_s, cmap=cmap_bias, norm=norm_bias, shading="auto", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)
            valid_pc_bias = pc_bias
            
        if valid_pc_val and valid_pc_bias:
            fig_sea.colorbar(valid_pc_val, ax=axes_sea[:2, :].ravel().tolist(), orientation="horizontal", shrink=0.5, pad=0.05, label=f"{unit}", extend=ext_val)
            fig_sea.colorbar(valid_pc_bias, ax=axes_sea[2, :].ravel().tolist(), orientation="horizontal", shrink=0.5, pad=0.05, label=f"Bias ({unit})", extend=ext_bias)
            
        fig_sea.suptitle(f"Seasonal Means ({year}) — {var.upper()} — RegCM vs {ref_name}", fontsize=18)
        
        valid_seasons_str = "_".join(season_data.keys())
        out_sea = cp.MAPS_DIR / f"{var}_{ref_name}_seasonal_{valid_seasons_str}_{year}.png"
        meta_sea = meta.copy()
        meta_sea["statistic"] = "seasonal_mean"
        save_figure_with_metadata(fig_sea, out_sea, meta_sea)
        print(f"  ✔ {out_sea.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=cp.YEAR_START)
    parser.add_argument("--vars", default=",".join(cp.VARIABLES))
    parser.add_argument("--partial", action="store_true", help="Allow partial period analysis")
    args = parser.parse_args()
    
    cp.MAPS_DIR.mkdir(parents=True, exist_ok=True)
    varlist = [v.strip() for v in args.vars.split(",")]
    
    print(f"\n{'═'*60}")
    print(f"  03_climatology_maps — year {args.year} (Partial: {args.partial})")
    print(f"{'═'*60}")
    
    for var in varlist:
        print(f"\n  ── {var} ──────────────────────")
        process_evaluation(var, args.year, args.partial)
        
    print(f"\n{'═'*60}\n  ✔  Maps complete — see {cp.MAPS_DIR}\n{'═'*60}\n")
