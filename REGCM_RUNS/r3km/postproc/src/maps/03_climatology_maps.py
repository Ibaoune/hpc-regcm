#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module - Climatology Maps (Period & Seasonal)
# ==============================================================================
"""
03_climatology_maps.py
======================
Generates integrated climatology evaluation figures (Observation, Model, Bias)
for an arbitrary date range. Supports Period Mean (1x3) and Seasonal (3x4) layouts.
"""

import sys, os, argparse, csv
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import src.commun.config_parser as cp
from src.commun.core.map_plotting import (
    get_geographic_extent, prepare_map_axis, plot_qa_check,
    HAS_CARTOPY
)
from src.commun.core.plot_style import apply_publication_style, get_variable_units, get_norm_and_cmap_for_var, get_nan_color

# Apply centralized styling
apply_publication_style()

def get_season_months(season):
    # DJF crosses years in processing, but definition is standard
    return cp.SEASONS.get(season, {"DJF":[12,1,2],"MAM":[3,4,5],"JJA":[6,7,8],"SON":[9,10,11]}[season])

def load_period_data(path_template_dir, var, years, start_date, end_date):
    paths = [path_template_dir / f"{y}.nc" for y in years]
    valid_paths = [p for p in paths if p.exists()]
    if not valid_paths:
        return None, None, None, None
        
    ds = xr.open_mfdataset(valid_paths, combine='by_coords')
    
    # Normalize time coordinate so daily datasets match regardless of timestamp hour (00:00 vs 12:00)
    ds['time'] = pd.to_datetime(ds['time'].values).normalize()
    
    # Subset time
    ds = ds.sel(time=slice(start_date, end_date))
    
    # Remove duplicate times if any
    _, index = np.unique(ds['time'], return_index=True)
    ds = ds.isel(time=index)
    ds = ds.sortby('time')
    
    data = ds[var].values
    time_vals = pd.to_datetime(ds['time'].values)
    
    lat = ds['lat'].values if 'lat' in ds else ds['xlat'].values
    lon = ds['lon'].values if 'lon' in ds else ds['xlon'].values
    
    if lat.ndim == 3:
        lat = lat[0]
    if lon.ndim == 3:
        lon = lon[0]
    
    ds.close()
    return data, lat, lon, time_vals

def compute_metrics(obs, mod):
    valid = np.isfinite(obs) & np.isfinite(mod)
    n = np.sum(valid)
    if n == 0:
        return np.nan, np.nan, np.nan, np.nan, 0
    o = obs[valid]
    m = mod[valid]
    bias = np.mean(m - o)
    mae = np.mean(np.abs(m - o))
    rmse = np.sqrt(np.mean((m - o)**2))
    corr = np.corrcoef(o, m)[0, 1] if n > 1 else np.nan
    return bias, mae, rmse, corr, n

def get_complete_seasons(time_vals, start_date, end_date):
    """
    Returns a dict mapping season string to list of time masks (one mask per complete occurrence).
    """
    seasons = ["DJF", "MAM", "JJA", "SON"]
    time_series = pd.Series(time_vals)
    
    season_masks = {s: [] for s in seasons}
    season_desc = {s: [] for s in seasons}
    
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    start_year = start_dt.year
    end_year = end_dt.year
    
    # DJF
    if start_year == end_year:
        # Règle pour une seule année : DJF regroupe Janvier, Février et Décembre de la même année
        y = start_year
        mask = (time_series.dt.month.isin([1, 2, 12]) & (time_series.dt.year == y)).values
        if mask.sum() > 0:
            season_masks["DJF"].append(mask)
            season_desc["DJF"].append(f"Jan, Feb, Dec {y} (Same-year DJF)")
    else:
        # Règle multi-années : D(Year-1), J(Year), F(Year)
        for y in range(start_year, end_year + 1):
            s_dt = pd.to_datetime(f"{y-1}-12-01")
            e_dt = pd.to_datetime(f"{y}-02-28") + pd.offsets.MonthEnd(0)
            if s_dt >= start_dt and e_dt <= end_dt:
                m1 = time_series.dt.month.isin([12]) & (time_series.dt.year == y - 1)
                m2 = time_series.dt.month.isin([1, 2]) & (time_series.dt.year == y)
                mask = (m1 | m2).values
                if mask.sum() > 0:
                    season_masks["DJF"].append(mask)
                    season_desc["DJF"].append(f"{y-1}-12-01 → {e_dt.strftime('%Y-%m-%d')}")
                
    # MAM, JJA, SON for each year
    for y in range(start_year, end_year + 1):
        # MAM
        s_dt = pd.to_datetime(f"{y}-03-01")
        e_dt = pd.to_datetime(f"{y}-05-31")
        if s_dt >= start_dt and e_dt <= end_dt:
            mask = time_series.dt.month.isin([3, 4, 5]) & (time_series.dt.year == y)
            mask = mask.values
            if mask.sum() > 0:
                season_masks["MAM"].append(mask)
                season_desc["MAM"].append(f"{s_dt.strftime('%Y-%m-%d')} → {e_dt.strftime('%Y-%m-%d')}")
                
        # JJA
        s_dt = pd.to_datetime(f"{y}-06-01")
        e_dt = pd.to_datetime(f"{y}-08-31")
        if s_dt >= start_dt and e_dt <= end_dt:
            mask = time_series.dt.month.isin([6, 7, 8]) & (time_series.dt.year == y)
            mask = mask.values
            if mask.sum() > 0:
                season_masks["JJA"].append(mask)
                season_desc["JJA"].append(f"{s_dt.strftime('%Y-%m-%d')} → {e_dt.strftime('%Y-%m-%d')}")
                
        # SON
        s_dt = pd.to_datetime(f"{y}-09-01")
        e_dt = pd.to_datetime(f"{y}-11-30")
        if s_dt >= start_dt and e_dt <= end_dt:
            mask = time_series.dt.month.isin([9, 10, 11]) & (time_series.dt.year == y)
            mask = mask.values
            if mask.sum() > 0:
                season_masks["SON"].append(mask)
                season_desc["SON"].append(f"{s_dt.strftime('%Y-%m-%d')} → {e_dt.strftime('%Y-%m-%d')}")
                
    return season_masks, season_desc


def process_evaluation(var, start_date, end_date, metrics_writer, allow_partial):
    cfg = cp.MODEL[var]
    unit_str = get_variable_units(var)
    
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    years = list(range(start_dt.year, end_dt.year + 1))
    
    is_special_year = (start_dt.month == 1 and start_dt.day == 1 and end_dt.month == 12 and end_dt.day == 31 and start_dt.year == end_dt.year)
    year_str = str(start_dt.year) if is_special_year else f"{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"
    title_period_str = str(start_dt.year) if is_special_year else f"{start_dt.strftime('%d %b %Y')}–{end_dt.strftime('%d %b %Y')}"
    period_label_str = "Annual" if is_special_year else "Period"
    
    print(f"\nRequested period: {start_date} → {end_date}")
    
    for ref_name, obs_cfg in cp.OBS[var].items():
        if obs_cfg.get("type") == "stations": continue
        
        mod_native_dir = cp.DATA_DIR / "processed" / "model" / var
        obs_native_dir = cp.DATA_DIR / "processed" / "obs" / ref_name / var
        mod_on_obs_dir = cp.DATA_DIR / "regridded" / ref_name / "model" / var
        
        m_nat_data, m_nat_lat, m_nat_lon, m_t = load_period_data(mod_native_dir, var, years, start_date, end_date)
        o_nat_data, o_nat_lat, o_nat_lon, o_t = load_period_data(obs_native_dir, var, years, start_date, end_date)
        m_rg_data, o_rg_lat, o_rg_lon, m_rg_t = load_period_data(mod_on_obs_dir, var, years, start_date, end_date)
        
        if m_nat_data is None or o_nat_data is None or m_rg_data is None:
            print(f"  ⚠  skipping {var} vs {ref_name}: data missing for requested period")
            continue
            
        common_times = np.intersect1d(m_t, o_t)
        if len(common_times) == 0:
            print(f"  ⚠  No overlapping dates between RegCM and {ref_name}. Skipping.")
            continue
            
        # Check partial period
        model_start, model_end = pd.to_datetime(m_t[0]).strftime('%Y-%m-%d'), pd.to_datetime(m_t[-1]).strftime('%Y-%m-%d')
        ref_start, ref_end = pd.to_datetime(o_t[0]).strftime('%Y-%m-%d'), pd.to_datetime(o_t[-1]).strftime('%Y-%m-%d')
        
        if (model_start > start_date or model_end < end_date) and not allow_partial:
            print(f"  ⚠  Requested period incomplete for model ({model_start} → {model_end}).")
            print("  Failing map job. Use --allow-partial-period to force.")
            sys.exit(1)
            
        print(f"  Model available date range:     {model_start} → {model_end}")
        print(f"  Reference available date range: {ref_start} → {ref_end}")
        print(f"  Common date range:              {pd.to_datetime(common_times[0]).strftime('%Y-%m-%d')} → {pd.to_datetime(common_times[-1]).strftime('%Y-%m-%d')}")
        print(f"  Number of common valid days:    {len(common_times)}")
        
        # Subset to common times
        m_mask = np.isin(m_t, common_times)
        o_mask = np.isin(o_t, common_times)
        m_rg_mask = np.isin(m_rg_t, common_times)
        
        m_nat_data = m_nat_data[m_mask]
        o_nat_data = o_nat_data[o_mask]
        m_rg_data = m_rg_data[m_rg_mask]
        
        # The common times sequence
        c_times = common_times
        
        try:
            with open(os.path.join(cp.POSTPROC_ROOT, "configs", "regions.yaml"), "r") as f:
                import yaml
                regions_cfg = yaml.safe_load(f)
                bbox = regions_cfg.get("MOROCCO", {}).get("DOMAIN_BBOX")
                if bbox:
                    extent = [bbox["lon_min"], bbox["lon_max"], bbox["lat_min"], bbox["lat_max"]]
                else:
                    extent = get_geographic_extent(m_nat_lon, m_nat_lat, o_nat_lon, o_nat_lat)
        except:
            extent = get_geographic_extent(m_nat_lon, m_nat_lat, o_nat_lon, o_nat_lat)
            
        if extent is None:
            print(f"  ⚠  Failed to determine valid extent for {var} vs {ref_name}. Skipping.")
            continue

        cmap_val, norm_val, extend_val, levels_val = get_norm_and_cmap_for_var(var, is_bias=False)
        cmap_bias, norm_bias, extend_bias, levels_bias = get_norm_and_cmap_for_var(var, is_bias=True)

        # ---------------------------------------------------------
        # PERIOD (ANNUAL) FIGURE (1x3)
        # ---------------------------------------------------------
        m_ann = np.nanmean(m_nat_data, axis=0)
        o_ann = np.nanmean(o_nat_data, axis=0)
        m_rg_ann = np.nanmean(m_rg_data, axis=0)
        
        bias_ann = np.where(np.isfinite(o_ann), m_rg_ann - o_ann, np.nan)
        
        try:
            plot_qa_check(f"{var}_{ref_name}_{year_str}", var, o_ann, o_nat_lon, o_nat_lat, ref_name, period_label_str)
            plot_qa_check(f"{var}_RegCM_{year_str}", var, m_ann, m_nat_lon, m_nat_lat, "RegCM", period_label_str)
        except ValueError as e:
            print(e)
            pass
            
        fig, axes = plt.subplots(1, 3, figsize=(15, 5), subplot_kw={"projection": ccrs.PlateCarree()} if HAS_CARTOPY else None)
        
        for ax in axes:
            prepare_map_axis(ax, extent, cp.cfg.get("plotting", {}))
            ax.set_facecolor(get_nan_color())
            
        if o_nat_lon.ndim == 1:
            o_lon_m, o_lat_m = np.meshgrid(o_nat_lon, o_nat_lat)
        else:
            o_lon_m, o_lat_m = o_nat_lon, o_nat_lat
            
        if o_rg_lon.ndim == 1:
            rg_lon_m, rg_lat_m = np.meshgrid(o_rg_lon, o_rg_lat)
        else:
            rg_lon_m, rg_lat_m = o_rg_lon, o_rg_lat
            
        pc1 = axes[0].pcolormesh(o_lon_m, o_lat_m, o_ann, cmap=cmap_val, norm=norm_val, shading="auto", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)
        axes[0].set_title(f"(a) {ref_name}")
        
        pc2 = axes[1].pcolormesh(m_nat_lon, m_nat_lat, m_ann, cmap=cmap_val, norm=norm_val, shading="auto", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)
        axes[1].set_title(f"(b) RegCM")
        
        pc3 = axes[2].pcolormesh(rg_lon_m, rg_lat_m, bias_ann, cmap=cmap_bias, norm=norm_bias, shading="auto", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)
        axes[2].set_title(f"(c) Bias")
        
        cbar_val = fig.colorbar(pc1, ax=axes[:2].tolist(), orientation="vertical", shrink=0.7, extend=extend_val, ticks=levels_val)
        cbar_val.set_label(f"{var.upper()} ({unit_str})")
        
        cbar_bias = fig.colorbar(pc3, ax=axes[2], orientation="vertical", shrink=0.7, extend=extend_bias, ticks=levels_bias)
        cbar_bias.set_label(f"Bias ({unit_str})")
        
        var_long = cp.MODEL[var].get('long_name', var.upper())
        fig.suptitle(f"{period_label_str} Mean {var_long} — {title_period_str}", fontsize=14, fontweight='bold', y=1.02)
        
        out_ann_png = cp.MAPS_DIR / f"{var}_{ref_name}_{period_label_str.lower()}_{year_str}.png"
        
        fig.savefig(out_ann_png, dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"  ✔ {out_ann_png.name}")
        
        bias, mae, rmse, corr, n_val = compute_metrics(o_ann, m_rg_ann)
        metrics_writer.writerow([var, ref_name, year_str, period_label_str, f"{bias:.3f}", f"{mae:.3f}", f"{rmse:.3f}", f"{corr:.3f}", n_val])

        # ---------------------------------------------------------
        # SEASONAL FIGURE (3x4)
        # ---------------------------------------------------------
        seasons = ["DJF", "MAM", "JJA", "SON"]
        
        season_masks, season_desc = get_complete_seasons(c_times, start_date, end_date)
        
        print("\n  Complete seasons included:")
        for s in seasons:
            print(f"  {s}:")
            for desc in season_desc[s]:
                print(f"      {desc}")
            print(f"      N seasons = {len(season_desc[s])}")
        
        season_data = {}
        for s in seasons:
            masks = season_masks[s]
            if len(masks) == 0:
                print(f"  ⚠  No complete {s} season found. Masking as NaN.")
                continue
                
            # Combine all complete occurrences (take mean over all valid days in those complete occurrences)
            combined_mask = np.zeros(len(c_times), dtype=bool)
            for m in masks:
                combined_mask |= m
                
            m_s = np.nanmean(m_nat_data[combined_mask], axis=0)
            o_s = np.nanmean(o_nat_data[combined_mask], axis=0)
            m_rg_s = np.nanmean(m_rg_data[combined_mask], axis=0)
            
            bias_s = np.where(np.isfinite(o_s), m_rg_s - o_s, np.nan)
            season_data[s] = (o_s, m_s, bias_s)
            
            s_bias, s_mae, s_rmse, s_corr, s_n = compute_metrics(o_s, m_rg_s)
            metrics_writer.writerow([var, ref_name, year_str, s, f"{s_bias:.3f}", f"{s_mae:.3f}", f"{s_rmse:.3f}", f"{s_corr:.3f}", s_n])
            
        if not season_data:
            print("  ⚠  No complete seasons at all. Skipping seasonal figure.")
            continue
            
        fig_sea, axes_sea = plt.subplots(3, 4, figsize=(16, 12), subplot_kw={"projection": ccrs.PlateCarree()} if HAS_CARTOPY else None)
        plt.subplots_adjust(wspace=0.05, hspace=0.1)
                
        for row_idx, row_label in enumerate([ref_name, "RegCM", "Bias"]):
            axes_sea[row_idx, 0].text(-0.15, 0.5, row_label, va='center', ha='right', rotation=90, 
                                      transform=axes_sea[row_idx, 0].transAxes, fontsize=12, fontweight='bold')
                                      
        valid_pc_val, valid_pc_bias = None, None
                
        for col_idx, s in enumerate(seasons):
            axes_sea[0, col_idx].set_title(s, fontsize=12, fontweight='bold')
            
            for row in range(3):
                ax = axes_sea[row, col_idx]
                prepare_map_axis(ax, extent, cp.cfg.get("plotting", {}))
                ax.set_facecolor(get_nan_color())
                
                if s not in season_data:
                    ax.text(0.5, 0.5, "No complete season", transform=ax.transAxes, ha='center', va='center', color='red')
                
            if s not in season_data: continue
            o_s, m_s, bias_s = season_data[s]
            
            valid_pc_val = axes_sea[0, col_idx].pcolormesh(o_lon_m, o_lat_m, o_s, cmap=cmap_val, norm=norm_val, shading="auto", transform=ccrs.PlateCarree())
            axes_sea[1, col_idx].pcolormesh(m_nat_lon, m_nat_lat, m_s, cmap=cmap_val, norm=norm_val, shading="auto", transform=ccrs.PlateCarree())
            valid_pc_bias = axes_sea[2, col_idx].pcolormesh(rg_lon_m, rg_lat_m, bias_s, cmap=cmap_bias, norm=norm_bias, shading="auto", transform=ccrs.PlateCarree())
            
        cbar_ax_val = fig_sea.add_axes([0.15, 0.05, 0.3, 0.02])
        cbar_ax_bias = fig_sea.add_axes([0.55, 0.05, 0.3, 0.02])
        
        if valid_pc_val is not None:
            cbar_val = fig_sea.colorbar(valid_pc_val, cax=cbar_ax_val, orientation='horizontal', extend=extend_val, ticks=levels_val)
            cbar_val.set_label(f"Seasonal {var.upper()} ({unit_str})")
        
        if valid_pc_bias is not None:
            cbar_bias = fig_sea.colorbar(valid_pc_bias, cax=cbar_ax_bias, orientation='horizontal', extend=extend_bias, ticks=levels_bias)
            cbar_bias.set_label(f"Seasonal Bias ({unit_str})")
            
        fig_sea.suptitle(f"Seasonal Mean {var_long} — {title_period_str}", fontsize=14, fontweight='bold', y=0.95)
        
        out_sea_png = cp.MAPS_DIR / f"{var}_{ref_name}_seasonal_{year_str}.png"
        
        fig_sea.savefig(out_sea_png, dpi=300, bbox_inches="tight")
        plt.close(fig_sea)
        print(f"  ✔ {out_sea_png.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--vars", default=",".join(cp.VARIABLES))
    parser.add_argument("--allow-partial-period", action="store_true")
    args = parser.parse_args()
    
    start_dt = pd.to_datetime(args.start_date)
    end_dt = pd.to_datetime(args.end_date)
    
    period_str = f"{args.start_date}_to_{args.end_date}"
    RESULTS_DIR = cp.POSTPROC_ROOT / "results" / period_str
    
    cp.MAPS_DIR = RESULTS_DIR / "maps"
    cp.MAPS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR = RESULTS_DIR / "metrics"
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    
    varlist = [v.strip() for v in args.vars.split(",")]
    
    is_special_year = (start_dt.month == 1 and start_dt.day == 1 and end_dt.month == 12 and end_dt.day == 31 and start_dt.year == end_dt.year)
    year_str = str(start_dt.year) if is_special_year else f"{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"
    
    print(f"\n{'═'*60}")
    print(f"  03_climatology_maps — {args.start_date} to {args.end_date}")
    print(f"{'═'*60}")
    
    metrics_path = METRICS_DIR / f"climatology_metrics_{year_str}.csv"
    with open(metrics_path, 'w', newline='') as csvfile:
        metrics_writer = csv.writer(csvfile)
        metrics_writer.writerow(["variable", "reference", "period", "season", "bias", "mae", "rmse", "correlation", "n_valid_cells"])
        
        for var in varlist:
            print(f"\n  ── {var} ──────────────────────")
            process_evaluation(var, args.start_date, args.end_date, metrics_writer, args.allow_partial_period)
            
    print(f"\n{'═'*60}\n  ✔  Maps complete — see {cp.MAPS_DIR}")
    print(f"  ✔  Metrics saved — see {METRICS_DIR}\n{'═'*60}\n")
