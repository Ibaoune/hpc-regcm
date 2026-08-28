import os
import glob
import argparse
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import pearsonr
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.commun import config_parser as cp
from src.commun.core.plot_style import apply_publication_style

apply_publication_style()

# Default configuration if not in yaml
DAY_START_HOUR_UTC = 0
MIN_STATION_COMPLETENESS = 0.90
WET_DAY_THRESHOLD = cp.cfg.get('daily_pdf', {}).get('wet_day_threshold', 0.1)
MAIN_BIN_WIDTH = cp.cfg.get('daily_pdf', {}).get('main_bin_width', 1.0)
LOW_INTENSITY_BIN_WIDTH = cp.cfg.get('daily_pdf', {}).get('inset_bin_width', 0.1)

OBS_CSV = "/home/mohammad.elaabaribao/lustre/climat-um6p-st-iwri-7ksifkvwkuy/shared/TEAM/data/Observed_data/ABH_stations_plusziz_and_abhbc1.csv"

def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    start_dt = pd.to_datetime(args.start_date)
    end_dt = pd.to_datetime(args.end_date)
    period_str = f"{args.start_date}_to_{args.end_date}"
    
    OUT_DIR = cp.POSTPROC_ROOT / "results" / period_str / "pdfs"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"=== Daily Station PDF Diagnostic ({period_str}) ===")
    print(f"Accumulation window starts at: {DAY_START_HOUR_UTC:02d}:00 UTC")
    
    years = list(range(start_dt.year, end_dt.year + 1))
    
    # 1. Read OBS
    df_obs = pd.read_csv(OBS_CSV)
    df_obs['Date'] = pd.to_datetime(df_obs['Date'])
    df_obs = df_obs[(df_obs['Date'] >= start_dt) & (df_obs['Date'] <= end_dt)].copy()
    df_obs['Precipitation'] = pd.to_numeric(df_obs['Precipitation'], errors='coerce')
    df_obs.loc[df_obs['Precipitation'] < 0, 'Precipitation'] = 0.0 # Cleanup negatives
    
    st_locs = df_obs.groupby('Station')[['Longitude', 'Latitude']].first().reset_index()
    
    # 2. Read RegCM coords
    regcm_files = []
    for y in years:
        glob_str = str(cp.POSTPROC_ROOT.parent / "T01" / "archive_periods" / f"{y}_all" / f"*_SHF.{y}*.nc")
        regcm_files.extend(sorted(glob.glob(glob_str)))
        
    if not regcm_files:
        raise ValueError(f"No RegCM files found for period {period_str}")
    ds_regcm = xr.open_dataset(regcm_files[0])
    regcm_lon = ds_regcm.xlon.values
    regcm_lat = ds_regcm.xlat.values
    ds_regcm.close()
    
    # 4. Spatial matching
    st_coords = []
    print("\nMatching stations spatially...")
    for idx, row in st_locs.iterrows():
        slon, slat = row['Longitude'], row['Latitude']
        if slat < regcm_lat.min() or slat > regcm_lat.max() or slon < regcm_lon.min() or slon > regcm_lon.max():
            continue
            
        dist_regcm = haversine(regcm_lon, regcm_lat, slon, slat)
        ry, rx = np.unravel_index(np.argmin(dist_regcm), dist_regcm.shape)
        d_regcm = dist_regcm[ry, rx]
        
        st_coords.append({
            'Station': row['Station'], 'lat': slat, 'lon': slon,
            'ry': ry, 'rx': rx, 'regcm_lat': regcm_lat[ry, rx], 'regcm_lon': regcm_lon[ry, rx], 'd_regcm': d_regcm
        })
    print(f"Total stations in domain: {len(st_coords)} out of {len(st_locs)}")
    
    for s in st_coords:
        if s['d_regcm'] > 10.0:
            print(f"  Suspicious distance for {s['Station']}: RegCM {s['d_regcm']:.1f}km")

    # 5. Extract RegCM
    print("\nExtracting RegCM timeseries...")
    regcm_times = []
    regcm_vals = []
    rys = np.array([s['ry'] for s in st_coords])
    rxs = np.array([s['rx'] for s in st_coords])
    
    for i, f in enumerate(regcm_files):
        try:
            ds = xr.open_dataset(f)
            regcm_times.append(ds.time.values)
            pr = ds['pr'].values
            pr_st = pr[:, rys, rxs]
            regcm_vals.append(pr_st * 3600.0)
            ds.close()
            if (i+1) % 50 == 0 or i == len(regcm_files)-1:
                print(f"  Processed {i+1}/{len(regcm_files)} files...")
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue
    
    regcm_times = np.concatenate(regcm_times)
    regcm_vals = np.concatenate(regcm_vals, axis=0)
    
    df_regcm_hr = pd.DataFrame(regcm_vals, columns=[s['Station'] for s in st_coords])
    
    # Only keep the times within start and end date
    df_regcm_hr['time'] = pd.to_datetime(regcm_times.astype(str))
    
    df_regcm_hr = df_regcm_hr[(df_regcm_hr['time'] >= start_dt) & (df_regcm_hr['time'] <= (end_dt + pd.Timedelta(days=1)))]
    
    # 7. Accumulate Daily
    print("Accumulating daily values...")
    def accumulate_daily(df):
        df['date'] = df['time'] - pd.Timedelta(hours=DAY_START_HOUR_UTC)
        df['date'] = df['date'].dt.floor('D')
        counts = df.groupby('date').count()
        sums = df.groupby('date').sum(numeric_only=True)
        invalid_days = counts[counts.iloc[:, 0] < 24].index
        sums.loc[invalid_days] = np.nan
        return sums

    regcm_daily = accumulate_daily(df_regcm_hr)
    
    # Drop duplicates in case the raw CSV has multiple entries for the same Date and Station
    df_obs = df_obs.drop_duplicates(subset=['Date', 'Station'])
    obs_pivot = df_obs.pivot(index='Date', columns='Station', values='Precipitation')
    obs_pivot = obs_pivot[[s['Station'] for s in st_coords]]
    
    # Completeness Check
    valid_obs_counts = obs_pivot.notna().sum()
    retained_stations = []
    rejected_stations = []
    for st in obs_pivot.columns:
        total_days = (end_dt - start_dt).days + 1
        if valid_obs_counts[st] / total_days >= MIN_STATION_COMPLETENESS:
            retained_stations.append(st)
        else:
            rejected_stations.append((st, valid_obs_counts[st]))
            
    print(f"\nStation Completeness Check (Threshold: {MIN_STATION_COMPLETENESS*100}%):")
    print(f"Retained: {len(retained_stations)}")
    print(f"Rejected: {len(rejected_stations)}")
    if rejected_stations:
        print("Rejected list:")
        for st, c in rejected_stations:
            print(f"  {st}: {c}/{total_days} days")
            
    # 8. Merge into paired common dataset
    regcm_melt = regcm_daily.reset_index().melt(id_vars='date', var_name='Station', value_name='regcm_pr_mmday')
    obs_melt = obs_pivot.reset_index().rename(columns={'Date': 'date'}).melt(id_vars='date', var_name='Station', value_name='obs_pr_mmday')
    
    merged = obs_melt.merge(regcm_melt, on=['date', 'Station'], how='inner')
    merged = merged[merged['Station'].isin(retained_stations)]
    
    # Drop rows where ANY model or obs is missing
    missing_mask = merged[['obs_pr_mmday', 'regcm_pr_mmday']].isna().any(axis=1)
    removed_count = missing_mask.sum()
    merged = merged.dropna(subset=['obs_pr_mmday', 'regcm_pr_mmday'])
    
    print(f"\nRemoved {removed_count} station-days due to missing OBS or incomplete model days.")
    
    # Merge Coordinates
    coord_df = pd.DataFrame(st_coords)
    merged = merged.merge(coord_df[['Station', 'lat', 'lon', 'd_regcm']], on='Station', how='left')
    
    # Save paired dataset (Optional, commented out for speed, can save if requested)
    # csv_path = OUT_DIR / f"paired_daily_precip_{year}_UTC{DAY_START_HOUR_UTC:02d}.csv"
    # merged.to_csv(csv_path, index=False)
    
    # 9. Examples
    print("\nExamples of matched daily values (first 5):")
    print(merged[['date', 'Station', 'obs_pr_mmday', 'regcm_pr_mmday']].head().to_string(index=False))
    
    # 10. QC Summary
    def get_qc(vals, name, unit="mm/day", is_obs=False):
        wet = vals[vals >= WET_DAY_THRESHOLD]
        mx = np.max(vals)
        mn = np.min(vals)
        wf = len(wet) / len(vals)
        p95 = np.percentile(wet, 95) if len(wet) > 0 else 0
        p99 = np.percentile(wet, 99) if len(wet) > 0 else 0
        p999 = np.percentile(wet, 99.9) if len(wet) > 0 else 0
        print(f"--- {name} ---")
        if is_obs: print(f"  Stations: {len(retained_stations)}")
        print(f"  Records: {len(vals)}")
        print(f"  Min/Max: {mn:.2f} / {mx:.2f} {unit}")
        print(f"  Wet fraction (>= {WET_DAY_THRESHOLD}mm/d): {wf:.4f}")
        print(f"  P95: {p95:.2f}, P99: {p99:.2f}, P99.9: {p999:.2f} (wet days only)")

    print("\n=== QC SUMMARY ===")
    get_qc(merged['obs_pr_mmday'].values, "OBS (Stations)", is_obs=True)
    get_qc(merged['regcm_pr_mmday'].values, "RegCM (~3 km)")
    
    # Write Extreme Metrics to CSV
    metrics_path = OUT_DIR / f"pr_station_intensity_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.csv"
    with open(metrics_path, "w") as f:
        f.write("dataset,n_samples,mean_wet_intensity,p95,p99,maximum\n")
        for name, vals in [("In-situ", merged['obs_pr_mmday'].values), ("RegCM_3km", merged['regcm_pr_mmday'].values)]:
            wet = vals[vals >= WET_DAY_THRESHOLD]
            n_samples = len(vals)
            mean_wet = np.mean(wet) if len(wet) > 0 else 0
            p95 = np.percentile(wet, 95) if len(wet) > 0 else 0
            p99 = np.percentile(wet, 99) if len(wet) > 0 else 0
            maximum = np.max(vals)
            f.write(f"{name},{n_samples},{mean_wet:.2f},{p95:.2f},{p99:.2f},{maximum:.2f}\n")
    print(f"Saved extreme metrics to {metrics_path}")
    
    # 11. Plot PDF
    obs_vals = merged['obs_pr_mmday'].values
    regcm_vals = merged['regcm_pr_mmday'].values
    
    max_val = max(np.max(obs_vals), np.max(regcm_vals))
    bins_main = np.arange(WET_DAY_THRESHOLD, max_val + MAIN_BIN_WIDTH, MAIN_BIN_WIDTH)
    bins_inset = np.arange(WET_DAY_THRESHOLD, 5.0 + LOW_INTENSITY_BIN_WIDTH, LOW_INTENSITY_BIN_WIDTH)
    
    def get_hist(vals, bins):
        wet = vals[vals >= WET_DAY_THRESHOLD]
        counts, edges = np.histogram(wet, bins=bins, density=True)
        centers = (edges[:-1] + edges[1:]) / 2
        return centers, counts
        
    c_obs, p_obs = get_hist(obs_vals, bins_main)
    c_reg, p_reg = get_hist(regcm_vals, bins_main)
    
    ci_obs, pi_obs = get_hist(obs_vals, bins_inset)
    ci_reg, pi_reg = get_hist(regcm_vals, bins_inset)
    
    # Figure 1: PDF
    fig, ax = plt.subplots(figsize=(7.5, 6))
    
    ax.plot(c_obs, p_obs, marker='o', linestyle='None', color='black', label='In situ', markersize=4, linewidth=1.2)
    ax.plot(c_reg, p_reg, marker='o', linestyle='None', color='darkorange', label='RegCM (~3 km)', markersize=4, linewidth=1.2)
    
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(left=WET_DAY_THRESHOLD)
    ax.set_xlabel('Daily precipitation (mm day⁻¹)', fontsize=12)
    ax.set_ylabel('Probability density', fontsize=12)
    ax.set_title(f'Daily Precipitation PDF at Rain-Gauge Locations — {start_dt.strftime("%Y-%m-%d")} to {end_dt.strftime("%Y-%m-%d")}', fontsize=12, fontweight='bold', pad=15)
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(True, which='major', linestyle='--', alpha=0.5, color='#b0b0b0')
    ax.grid(False, which='minor')
    
    # Inset
    ins_ax = ax.inset_axes([0.1, 0.1, 0.35, 0.35])
    ins_ax.plot(ci_obs, pi_obs, marker='o', linestyle='None', color='black', markersize=3, linewidth=1)
    ins_ax.plot(ci_reg, pi_reg, marker='o', linestyle='None', color='darkorange', markersize=3, linewidth=1)
    ins_ax.set_xlim(WET_DAY_THRESHOLD, 5)
    ins_ax.set_title('Low intensity', fontsize=10, fontweight='bold')
    ins_ax.grid(True, which='major', linestyle='--', alpha=0.5, color='#b0b0b0')
    ins_ax.grid(False, which='minor')
    
    pdf_path = OUT_DIR / f"pr_daily_pdf_insitu_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.png"
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\nSaved PDF to {pdf_path}")
    
    # Figure 2: Wet Day Frequency Barplot is not required per new instructions, skipping.
    # Station-level metrics are skipped as well as we only need the global extreme metrics saved above.

if __name__ == "__main__":
    main()
