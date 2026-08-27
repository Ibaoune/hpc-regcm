#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
"""
09_domain_overview.py
=====================
Produces Figure 1: Scientific evaluation domain, sponge zone, topography, and station locations.
"""

import sys, os, argparse
import pandas as pd
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.config_parser as cp
from src.core.map_plotting import (
    prepare_map_axis, get_colormap_norm, save_figure_with_metadata, HAS_CARTOPY
)
import cartopy.crs as ccrs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=cp.YEAR_START)
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()

    OUT_DIR = cp.RESULTS_DIR / "domain"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'═'*60}")
    print(f"  09_domain_overview")
    print(f"{'═'*60}")

    # To get topography and coordinates, we can load the first original RegCM output
    raw_f = cp.OUTPUT_DIR
    import glob
    raw_files = sorted(glob.glob(f"{raw_f}/*STS*.nc"))
    
    if not raw_files:
        print("  ⚠  No raw RegCM outputs found to extract topography.")
        sys.exit(1)
        
    with nc.Dataset(raw_files[0]) as ds:
        xlat = ds.variables.get("lat", ds.variables.get("xlat"))[:]
        xlon = ds.variables.get("lon", ds.variables.get("xlon"))[:]
        topo = ds.variables.get("topo", None)
        if topo is not None:
            topo = topo[:]

    # Load Stations
    abh_cfg = cp.cfg.get("datasets", {}).get("ABH", {})
    abh_path = abh_cfg.get("path")
    stat_lats, stat_lons = [], []

    if abh_path and os.path.exists(abh_path):
        df = pd.read_csv(abh_path)
        df_u = df.drop_duplicates(subset=["Station"])
        stat_lats = df_u["Latitude"].values
        stat_lons = df_u["Longitude"].values

    sponge = cp.cfg.get("domain", {}).get("boundary_trim", {}).get("cells", 30)

    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={"projection": ccrs.PlateCarree()} if HAS_CARTOPY else None)
    
    # We want a regional geographic context, so we add a buffer around the full computational domain
    extent = [float(xlon.min() - 5), float(xlon.max() + 5), float(xlat.min() - 5), float(xlat.max() + 5)]
    prepare_map_axis(ax, extent, cp.cfg.get("plotting", {}))

    # Topography
    if topo is not None:
        cmap_topo, norm_topo, _, ext_topo = get_colormap_norm("elevation", False, cp.cfg.get("plotting", {}))
        pc = ax.pcolormesh(xlon, xlat, topo, cmap=cmap_topo, norm=norm_topo, shading="auto", 
                           transform=ccrs.PlateCarree() if HAS_CARTOPY else None, alpha=0.8)
        fig.colorbar(pc, ax=ax, shrink=0.7, pad=0.05, label="Elevation (m)", extend=ext_topo)

    # Full Domain Outline
    lons_bound = np.concatenate([xlon[0,:], xlon[:,-1], xlon[-1,::-1], xlon[::-1,0]])
    lats_bound = np.concatenate([xlat[0,:], xlat[:,-1], xlat[-1,::-1], xlat[::-1,0]])
    
    ax.plot(lons_bound, lats_bound, color="black", lw=2.5, label="RegCM Computational Domain", 
            transform=ccrs.PlateCarree() if HAS_CARTOPY else None)

    # Sponge zone (Inner domain)
    lons_sp = np.concatenate([xlon[sponge,sponge:-sponge], xlon[sponge:-sponge,-sponge-1], 
                              xlon[-sponge-1,-sponge-1:sponge:-1], xlon[-sponge-1:sponge:-1,sponge]])
    lats_sp = np.concatenate([xlat[sponge,sponge:-sponge], xlat[sponge:-sponge,-sponge-1], 
                              xlat[-sponge-1,-sponge-1:sponge:-1], xlat[-sponge-1:sponge:-1,sponge]])
                              
    ax.plot(lons_sp, lats_sp, color="red", linestyle="--", lw=2, 
            label=f"Inner Domain (excluding {sponge}-cell sponge)", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)

    # Scientific Evaluation Region (Morocco Box)
    b_min_lon = cp.DOMAIN_BBOX['lon_min']
    b_max_lon = cp.DOMAIN_BBOX['lon_max']
    b_min_lat = cp.DOMAIN_BBOX['lat_min']
    b_max_lat = cp.DOMAIN_BBOX['lat_max']
    
    eval_lons = [b_min_lon, b_max_lon, b_max_lon, b_min_lon, b_min_lon]
    eval_lats = [b_min_lat, b_min_lat, b_max_lat, b_max_lat, b_min_lat]
    
    ax.plot(eval_lons, eval_lats, color="blue", linestyle="-", lw=2.5,
            label="Scientific Evaluation Box", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)

    # Stations
    if len(stat_lons) > 0:
        ax.scatter(stat_lons, stat_lats, c="yellow", edgecolors="black", s=30, marker="o", 
                   label="ABH Stations", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)

    ax.legend(loc="lower right", framealpha=0.9, fontsize=11)
    ax.set_title("RegCM r3km Simulation Domain & Geographic Context", fontsize=16, fontweight="bold")

    out = OUT_DIR / "regcm_r3km_domain_overview.png"
    meta = {
        "config_hash": cp.get_config_hash(),
        "extent": extent
    }
    save_figure_with_metadata(fig, out, meta)
    print(f"  ✔ {out.name}")

if __name__ == "__main__":
    main()
