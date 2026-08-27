#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
"""
08_station_validation.py
========================
Validates RegCM precipitation against ABH in-situ stations.
Extracts nearest grid cells without interpolation.
Plots a centralized station map using map_plotting.py.
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
import src.metrics_engine as me
from src.core.map_plotting import (
    get_geographic_extent, prepare_map_axis, get_colormap_norm,
    save_figure_with_metadata, HAS_CARTOPY
)
import cartopy.crs as ccrs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=cp.YEAR_START)
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    YEAR = args.year

    STAT_DIR = cp.RESULTS_DIR / "stations" / "pr"
    STAT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'═'*60}")
    print(f"  08_station_validation — year {YEAR} (Partial: {args.partial})")
    print(f"{'═'*60}")

    mod_f = cp.DATA_DIR / "processed" / "model" / "pr" / f"{YEAR}.nc"
    if not mod_f.exists():
        print("  ⚠  Model PR file missing. Run 01_preprocess first.")
        sys.exit(1)
        
    with nc.Dataset(mod_f) as ds:
        mod_data = ds.variables["pr"][:]
        xlat = ds.variables.get("lat", ds.variables.get("xlat"))[:]
        xlon = ds.variables.get("lon", ds.variables.get("xlon"))[:]
        t_mod = ds.variables["time"][:]
        t_units = ds.variables["time"].units
        dates_mod = nc.num2date(t_mod, t_units, calendar="standard")
        
    mod_date_strs = [f"{d.year:04d}-{d.month:02d}-{d.day:02d}" for d in dates_mod]
    mod_date_idx = {d: i for i, d in enumerate(mod_date_strs)}

    abh_cfg = cp.cfg.get("datasets", {}).get("ABH", {})
    abh_path = abh_cfg.get("path")

    if not abh_path or not os.path.exists(abh_path):
        print("  ⚠  ABH station data not found.")
        sys.exit(1)

    import glob
    raw_files = sorted(glob.glob(f"{cp.OUTPUT_DIR}/*STS*.nc"))
    topo = None
    if raw_files:
        with nc.Dataset(raw_files[0]) as ds_r:
            t_var = ds_r.variables.get("topo")
            if t_var is not None:
                topo = t_var[:]

    df = pd.read_csv(abh_path)
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    df = df[df["Date"].str.startswith(str(YEAR))]

    stations = df["Station"].unique()

    sponge = cp.cfg.get("domain", {}).get("boundary_trim", {}).get("cells", 30)
    ny, nx = xlat.shape

    results = []
    excluded = []
    qc_daily = cp.cfg.get("stations", {}).get("daily_metrics", {}).get("minimum_valid_fraction", 0.90)

    for stat in stations:
        sdf = df[df["Station"] == stat]
        slat = sdf["Latitude"].iloc[0]
        slon = sdf["Longitude"].iloc[0]
        
        dlat = (xlat - slat) * 111.0
        dlon = (xlon - slon) * 111.0 * np.cos(np.deg2rad(slat))
        dist = np.sqrt(dlat**2 + dlon**2)
        
        j, i = np.unravel_index(np.argmin(dist), dist.shape)
        min_dist = dist[j, i]
        
        if j < sponge or j >= ny - sponge or i < sponge or i >= nx - sponge:
            excluded.append({"Station": stat, "Lat": slat, "Lon": slon, "Reason": f"Inside sponge zone (dist={min_dist:.1f}km)"})
            continue
            
        m_ts_full = mod_data[:, j, i]
        
        o_ts = []
        m_ts = []
        
        expected = len(mod_date_strs)
        observed = len(sdf)
        
        for _, row in sdf.iterrows():
            d_str = row["Date"]
            o_val = row["Precipitation"]
            if d_str in mod_date_idx:
                idx = mod_date_idx[d_str]
                m_val = m_ts_full[idx]
                if np.isfinite(o_val) and np.isfinite(m_val):
                    o_ts.append(o_val)
                    m_ts.append(m_val)
                    
        n_valid = len(o_ts)
        valid_fraction = n_valid / expected if expected > 0 else 0
        
        if valid_fraction < qc_daily:
            excluded.append({"Station": stat, "Lat": slat, "Lon": slon, "Reason": f"Valid fraction {valid_fraction:.2f} < {qc_daily} (N={n_valid})"})
            continue
            
        t_mets = me.compute_temporal_metrics(np.array(o_ts), np.array(m_ts))
        
        results.append({
            "Station": stat,
            "Lat": slat,
            "Lon": slon,
            "Grid_Dist_km": min_dist,
            "N_expected": expected,
            "N_observed": observed,
            "N_valid_pairs": n_valid,
            "Valid_Fraction": valid_fraction,
            "Mean_Obs": np.mean(o_ts),
            "Mean_Mod": np.mean(m_ts),
            "MB": t_mets["MB"],
            "MAE": t_mets["MAE"],
            "RMSE": t_mets["RMSE"],
            "r": t_mets["r"]
        })

    res_df = pd.DataFrame(results)
    excl_df = pd.DataFrame(excluded)
    
    if len(res_df) > 0:
        res_df.to_csv(STAT_DIR / f"pr_station_metrics_{YEAR}.csv", index=False)
        print(f"  ✔ Validated {len(res_df)} stations.")
        
    if len(excl_df) > 0:
        excl_df.to_csv(STAT_DIR / "excluded_stations.csv", index=False)
        print(f"  ✔ Excluded {len(excl_df)} stations.")

    # -------------------------------------------------------------
    # Plotting Station Map using map_plotting.py
    # -------------------------------------------------------------
    if len(res_df) > 0:
        all_lons = list(res_df["Lon"]) + (list(excl_df["Lon"]) if len(excl_df) > 0 else [])
        all_lats = list(res_df["Lat"]) + (list(excl_df["Lat"]) if len(excl_df) > 0 else [])
        
        extent = get_geographic_extent(np.array(all_lons), np.array(all_lats))
        if extent is None:
            extent = [cp.DOMAIN_BBOX['lon_min'], cp.DOMAIN_BBOX['lon_max'], cp.DOMAIN_BBOX['lat_min'], cp.DOMAIN_BBOX['lat_max']]

        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={"projection": ccrs.PlateCarree()} if HAS_CARTOPY else None)
        prepare_map_axis(ax, extent, cp.cfg.get("plotting", {}))
        
        cmap, norm, levels, ext = get_colormap_norm("pr", True, cp.cfg.get("plotting", {}))

        # Topography
        if topo is not None:
            cmap_topo, norm_topo, _, _ = get_colormap_norm("elevation", False, cp.cfg.get("plotting", {}))
            ax.pcolormesh(xlon, xlat, topo, cmap=cmap_topo, norm=norm_topo, shading="auto", 
                          transform=ccrs.PlateCarree() if HAS_CARTOPY else None, alpha=0.5)

        # Scientific Evaluation Region
        b_min_lon = cp.DOMAIN_BBOX['lon_min']
        b_max_lon = cp.DOMAIN_BBOX['lon_max']
        b_min_lat = cp.DOMAIN_BBOX['lat_min']
        b_max_lat = cp.DOMAIN_BBOX['lat_max']
        eval_lons = [b_min_lon, b_max_lon, b_max_lon, b_min_lon, b_min_lon]
        eval_lats = [b_min_lat, b_min_lat, b_max_lat, b_max_lat, b_min_lat]
        ax.plot(eval_lons, eval_lats, color="blue", linestyle="--", lw=1.5,
                label="Evaluation Box", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)

        # Plot excluded stations
        if len(excl_df) > 0:
            ax.scatter(excl_df["Lon"], excl_df["Lat"], marker="x", color="gray", s=30, label="Excluded", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)

        # Plot valid stations
        sc = ax.scatter(res_df["Lon"], res_df["Lat"], c=res_df["MB"], cmap=cmap, norm=norm,
                        s=60, edgecolors="k", lw=0.5, label="Included", transform=ccrs.PlateCarree() if HAS_CARTOPY else None)
        
        # Colorbar
        cbar = fig.colorbar(sc, ax=ax, shrink=0.7, pad=0.05, extend=ext)
        cbar.set_label("Bias (mm/day)")
        
        # Title
        n_start, n_end = (mod_date_strs[0], mod_date_strs[-1]) if mod_date_strs else ("Unknown", "Unknown")
        title_period = f"{n_start} to {n_end}" if args.partial else f"{YEAR}"
        title_str = f"Station Bias — PR — {title_period}\nAccepted: {len(res_df)} | Excluded: {len(excl_df)}"
        ax.set_title(title_str, fontsize=14, fontweight="bold")
        ax.legend(loc="lower left", frameon=True)
        
        out_map = STAT_DIR / f"pr_station_bias_{YEAR}.png"
        meta = {
            "config_hash": cp.get_config_hash(),
            "variable": "pr",
            "statistic": "bias",
            "period": title_period,
            "extent": extent
        }
        save_figure_with_metadata(fig, out_map, meta)
        print(f"  ✔ Map saved to {out_map.name}.")

if __name__ == "__main__":
    main()
