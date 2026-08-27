#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
"""
10_precipitation_pdf.py
=======================
Produces precipitation intensity PDFs (spatial density distribution)
comparing RegCM outputs with observations over the scientific evaluation domain.
"""

import sys, os, argparse
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.config_parser as cp
from src.core.map_plotting import save_figure_with_metadata

def get_proportions(data, bins):
    counts, edges = np.histogram(data, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2.0
    proportions = counts / len(data)
    # Mask zero counts for log plotting
    mask = proportions > 0
    return centers[mask], proportions[mask]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=cp.YEAR_START)
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    
    YEAR = args.year
    OUT_DIR = cp.RESULTS_DIR / "pdfs"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'═'*60}")
    print(f"  10_precipitation_pdf — year {YEAR}")
    print(f"{'═'*60}")
    
    # Check if pr is active
    if "pr" not in cp.VARIABLES:
        print("  ⚠  pr is not active in variables.yaml. Skipping.")
        sys.exit(0)
        
    mod_file = cp.DATA_DIR / "processed" / "model" / "pr" / f"{YEAR}.nc"
    obs_file = cp.DATA_DIR / "regridded" / "model" / "MSWEP" / "pr" / f"{YEAR}.nc"
    
    if not mod_file.exists():
        print(f"  ⚠  Missing {mod_file}")
        sys.exit(1)
        
    has_obs = obs_file.exists()
    
    print("  loading data...")
    with nc.Dataset(mod_file) as ds:
        mod_data = ds.variables["pr"][:]
        xlat = ds.variables.get("lat", ds.variables.get("xlat"))[:]
        xlon = ds.variables.get("lon", ds.variables.get("xlon"))[:]
        
    obs_data = None
    if has_obs:
        with nc.Dataset(obs_file) as ds:
            obs_data = ds.variables["pr"][:]
            
    # Mask using DOMAIN_BBOX
    b_min_lon = cp.DOMAIN_BBOX['lon_min']
    b_max_lon = cp.DOMAIN_BBOX['lon_max']
    b_min_lat = cp.DOMAIN_BBOX['lat_min']
    b_max_lat = cp.DOMAIN_BBOX['lat_max']
    
    eval_mask = (xlat >= b_min_lat) & (xlat <= b_max_lat) & (xlon >= b_min_lon) & (xlon <= b_max_lon)
    
    # Flatten and remove NaNs and zeros/negatives
    mod_flat = mod_data[:, eval_mask].flatten()
    mod_flat = mod_flat[np.isfinite(mod_flat) & (mod_flat >= 0.1)]
    
    if has_obs:
        obs_flat = obs_data[:, eval_mask].flatten()
        obs_flat = obs_flat[np.isfinite(obs_flat) & (obs_flat >= 0.1)]
        
    # Setup Figure
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Bins
    bins_main = np.arange(0.1, 150.0, 1.0)
    bins_inset = np.arange(0.1, 3.1, 0.1)
    
    # Main Plot
    c_mod, p_mod = get_proportions(mod_flat, bins_main)
    ax.scatter(c_mod, p_mod, c="orange", s=20, label="RegCM-r3km", zorder=3)
    
    if has_obs:
        c_obs, p_obs = get_proportions(obs_flat, bins_main)
        ax.scatter(c_obs, p_obs, c="black", s=20, label="MSWEP", zorder=2)
        
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.1, 200)
    ax.set_ylim(1e-9, 1e0)
    ax.grid(True, which="major", ls="-", color="lightgray")
    ax.grid(True, which="minor", ls=":", color="whitesmoke")
    ax.set_facecolor("#EAEAF2")
    
    ax.set_xlabel("Precipitation intensity (mm/day)", fontsize=12)
    ax.set_ylabel("Proportions", fontsize=12)
    ax.set_title(f"PDFs of daily precipitation — {YEAR}", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", frameon=True, fontsize=11)
    
    # Inset Plot
    axins = inset_axes(ax, width="35%", height="35%", loc="lower left", borderpad=2.5)
    
    c_mod_i, p_mod_i = get_proportions(mod_flat, bins_inset)
    axins.scatter(c_mod_i, p_mod_i, c="orange", s=10)
    
    if has_obs:
        c_obs_i, p_obs_i = get_proportions(obs_flat, bins_inset)
        axins.scatter(c_obs_i, p_obs_i, c="black", s=10)
        
    axins.set_xscale("log")
    axins.set_yscale("log")
    axins.set_xlim(0.1, 3.0)
    axins.set_ylim(1e-4, 1e0)
    axins.grid(True, which="both", ls="-", color="lightgray", lw=0.5)
    axins.set_facecolor("#EAEAF2")
    
    # Add text for bin sizes
    plt.figtext(0.65, 0.35, "PDFs of daily precipitation\nBin size: 1.0 mm/day (main)\n          0.1 mm/day (inset)", fontsize=10, ha="left", bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"))
    
    out_map = OUT_DIR / f"pr_intensity_pdf_{YEAR}.png"
    meta = {
        "config_hash": cp.get_config_hash(),
        "variable": "pr",
        "statistic": "pdf",
        "period": str(YEAR)
    }
    save_figure_with_metadata(fig, out_map, meta)
    print(f"  ✔ Map saved to {out_map.name}.")

if __name__ == "__main__":
    main()
