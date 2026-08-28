#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: Hourly Precipitation PDF Diagnostic
# ==============================================================================
"""
04_hourly_precip_pdf.py
=======================
Extracts hourly RegCM and ERA5 precipitation, harmonizes temporal steps,
applies the spatial mask (Morocco), and computes non-smoothed marker-based
PDFs with log-log scaling.

Generates two variants:
A. Native-resolution distribution (RegCM 3km vs ERA5 31km)
B. Common-grid distribution (RegCM 3km aggregated to ERA5 31km grid)
"""

import os
import sys
import yaml
import glob
import logging
import argparse
import numpy as np
import pandas as pd
import xarray as xr
import cartopy.io.shapereader as shpreader
from matplotlib.path import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import src.commun.config_parser as cp
from src.commun.core.plot_style import apply_publication_style

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

apply_publication_style()

# Constants
ERA5_DIR = "/home/mohammad.elaabaribao/lustre/climat-um6p-st-iwri-7ksifkvwkuy/shared/TEAM/data/ERA5/from_khadija/hourly"
REGIONS_CONFIG = os.path.join(cp.POSTPROC_ROOT, "configs", "regions.yaml")

def get_mask_2d(lon_2d, lat_2d, geometry):
    """Create a 2D boolean mask from a geopandas geometry."""
    logger.info("Computing 2D spatial mask from geometry...")
    pts = np.column_stack((lon_2d.ravel(), lat_2d.ravel()))
    mask = np.zeros(pts.shape[0], dtype=bool)
    
    if geometry.geom_type == 'Polygon':
        polys = [geometry]
    else:
        polys = geometry.geoms
        
    for poly in polys:
        ext = np.asarray(poly.exterior.coords)
        path = Path(ext)
        mask |= path.contains_points(pts)
        for interior in poly.interiors:
            path_in = Path(np.asarray(interior.coords))
            mask &= ~path_in.contains_points(pts)
            
    return mask.reshape(lon_2d.shape)

def get_mask_1d(lon_1d, lat_1d, geometry):
    lon_2d, lat_2d = np.meshgrid(lon_1d, lat_1d)
    return get_mask_2d(lon_2d, lat_2d, geometry)

def extract_wet_values_native(file_path, valid_times, var_name, mask, factor, is_era5=False, threshold=0.1):
    try:
        ds = xr.open_dataset(file_path)
    except Exception as e:
        logger.error(f"Failed to open {file_path}: {e}")
        return np.array([]), np.array([])
        
    intersect_times = np.intersect1d(ds.time.values, valid_times)
    if len(intersect_times) == 0:
        ds.close()
        return np.array([]), np.array([])
        
    ds = ds.sel(time=intersect_times)
    vals = ds[var_name].values
    mask_3d = np.broadcast_to(mask, vals.shape)
    valid_vals = vals[mask_3d] * factor
    wet_vals = valid_vals[valid_vals >= threshold]
    ds.close()
    return wet_vals, intersect_times

def aggregate_regcm_to_era5(regcm_vals, regcm_mask, era5_mask, era5_lat, era5_lon, regcm_lat, regcm_lon):
    """
    Approximates aggregation by binning RegCM cells into ERA5 grid cells.
    Since ERA5 is ~0.25 deg (31km) and RegCM is 3km, we average RegCM points inside each ERA5 box.
    """
    logger.info("Aggregating RegCM to ERA5 common grid...")
    # This is a simplified nearest-neighbor/binning approach for demonstration.
    # In a full pipeline, we'd use xESMF conservative regridding.
    # Since bounds are missing, we use KDTree to map RegCM centers to nearest ERA5 center.
    from scipy.spatial import cKDTree
    
    e_lon2d, e_lat2d = np.meshgrid(era5_lon, era5_lat)
    era5_pts = np.column_stack([e_lon2d.ravel(), e_lat2d.ravel()])
    regcm_pts = np.column_stack([regcm_lon.ravel(), regcm_lat.ravel()])
    
    tree = cKDTree(era5_pts)
    _, indices = tree.query(regcm_pts)
    
    # We want to compute the mean of RegCM values for each ERA5 grid cell
    ntime = regcm_vals.shape[0]
    agg_vals = np.zeros((ntime, len(era5_pts)), dtype=np.float32)
    counts = np.bincount(indices, minlength=len(era5_pts))
    valid_cells = counts > 0
    
    # Flatten RegCM spatial dims
    flat_regcm = regcm_vals.reshape(ntime, -1)
    
    # Sum over indices
    for t in range(ntime):
        agg_vals[t, :] = np.bincount(indices, weights=flat_regcm[t, :], minlength=len(era5_pts))
        
    # Average
    agg_vals[:, valid_cells] /= counts[valid_cells]
    agg_vals[:, ~valid_cells] = np.nan
    
    agg_vals_3d = agg_vals.reshape((ntime, era5_lat.shape[0], era5_lon.shape[0]))
    
    # Extract using ERA5 mask
    mask_3d = np.broadcast_to(era5_mask, agg_vals_3d.shape)
    valid_vals = agg_vals_3d[mask_3d]
    return valid_vals[valid_vals >= 0.1]

def process_pdfs(start_date, end_date, region, threshold=0.1):
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    years = list(range(start_dt.year, end_dt.year + 1))
    period_str = f"{start_date}_to_{end_date}"
    
    logger.info(f"Starting Hourly PDF Diagnostic for period: {period_str}, Region: {region}")
    
    out_dir = cp.POSTPROC_ROOT / "results" / period_str / "pdfs"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Load Shapefile using Cartopy
    if region.lower() == "morocco":
        shpfilename = shpreader.natural_earth(resolution='110m', category='cultural', name='admin_0_countries')
        reader = shpreader.Reader(shpfilename)
        geom = None
        for country in reader.records():
            if country.attributes.get('NAME', '') == 'Morocco' or country.attributes.get('ADMIN', '') == 'Morocco':
                geom = country.geometry
                break
        if geom is None:
            logger.error("Morocco not found in Natural Earth database.")
            sys.exit(1)
    else:
        logger.error(f"Region {region} not currently supported by cartopy natural_earth hardcode.")
        sys.exit(1)
    
    bins_main = np.arange(0.5, 250.5, 0.5)
    bins_inset = np.arange(0.1, 5.1, 0.1)
    
    regcm_wet_native_all = []
    regcm_wet_agg_all = []
    era5_wet_all = []
    
    regcm_total_valid_hours = 0
    era5_total_valid_hours = 0
    
    regcm_mask = None
    regcm_lat, regcm_lon = None, None
    era5_mask = None
    era5_lat, era5_lon = None, None
    
    for y in years:
        logger.info(f"--- Processing Year {y} ---")
        
        era5_file = os.path.join(ERA5_DIR, f"era5_{y}.nc")
        if not os.path.exists(era5_file):
            logger.warning(f"ERA5 file missing for {y}")
            continue
            
        era5_ds_tmp = xr.open_dataset(era5_file)
        era5_times_yr = era5_ds_tmp.time.values
        era5_lat, era5_lon = era5_ds_tmp.latitude.values, era5_ds_tmp.longitude.values
        era5_mask = get_mask_1d(era5_lon, era5_lat, geom)
        era5_ds_tmp.close()
        
        archive_dir = cp.POSTPROC_ROOT.parent / cp.SIM_NAME / "archive_periods" / f"{y}_all"
        logger.info(f"Looking for RegCM files in: {archive_dir}")
        regcm_files = sorted(glob.glob(str(archive_dir / f"test_001_SHF.{y}*.nc")))
        logger.info(f"Found {len(regcm_files)} RegCM files matching test_001_SHF.{y}*.nc")
        if not regcm_files:
            continue
        
        if regcm_mask is None:
            ds_ref = xr.open_dataset(regcm_files[0])
            regcm_lat, regcm_lon = ds_ref.xlat.values, ds_ref.xlon.values
            regcm_mask = get_mask_2d(regcm_lon, regcm_lat, geom)
            ds_ref.close()
            
        valid_times_for_year = []
        regcm_wet_nat_yr = []
        regcm_wet_agg_yr = []
        
        logger.info(f"Extracting RegCM data ({len(regcm_files)} files)...")
        for fpath in tqdm(regcm_files, desc="RegCM Files"):
            ds = xr.open_dataset(fpath)
            intersect_times = np.intersect1d(ds.time.values, era5_times_yr)
            if len(intersect_times) > 0:
                ds = ds.sel(time=intersect_times)
                vals = ds["pr"].values * 3600.0 # kg/m2/s to mm/h
                
                # Native
                mask_3d = np.broadcast_to(regcm_mask, vals.shape)
                valid_vals = vals[mask_3d]
                regcm_wet_nat_yr.append(valid_vals[valid_vals >= threshold])
                
                # Aggregated
                agg_wet = aggregate_regcm_to_era5(vals, regcm_mask, era5_mask, era5_lat, era5_lon, regcm_lat, regcm_lon)
                regcm_wet_agg_yr.append(agg_wet)
                
                valid_times_for_year.extend(intersect_times)
            ds.close()
                
        valid_times_for_year = np.array(valid_times_for_year)
        regcm_total_valid_hours += len(valid_times_for_year)
        if regcm_wet_nat_yr:
            regcm_wet_native_all.append(np.concatenate(regcm_wet_nat_yr))
            regcm_wet_agg_all.append(np.concatenate(regcm_wet_agg_yr))
        
        logger.info("Extracting ERA5 data...")
        wvals_e, vtimes_e = extract_wet_values_native(era5_file, valid_times_for_year, "tp", era5_mask, 1000.0, is_era5=True, threshold=threshold)
        if len(wvals_e) > 0:
            era5_wet_all.append(wvals_e)
        era5_total_valid_hours += len(vtimes_e)
        
    if not era5_wet_all:
        logger.error("No valid data extracted. Exiting.")
        return
        
    regcm_nat_pooled = np.concatenate(regcm_wet_native_all)
    regcm_agg_pooled = np.concatenate(regcm_wet_agg_all)
    era5_pooled = np.concatenate(era5_wet_all)
    
    title_period = f"{start_date} to {end_date}"
    
    # We will generate two plots: Native and Common-Grid
    def plot_pdf(regcm_data, era5_data, variant_name, regcm_label, samples_regcm, samples_era5):
        hist_r_m, _ = np.histogram(regcm_data, bins=bins_main, density=True)
        hist_e_m, _ = np.histogram(era5_data, bins=bins_main, density=True)
        hist_r_i, _ = np.histogram(regcm_data, bins=bins_inset, density=True)
        hist_e_i, _ = np.histogram(era5_data, bins=bins_inset, density=True)
        
        pdf_r_m = hist_r_m
        pdf_e_m = hist_e_m
        pdf_r_i = hist_r_i
        pdf_e_i = hist_e_i
        
        fig, ax = plt.subplots(figsize=(7.5, 6))
        
        bcm = (bins_main[:-1] + bins_main[1:]) / 2
        bci = (bins_inset[:-1] + bins_inset[1:]) / 2
        
        rv = pdf_r_m > 0
        ev = pdf_e_m > 0
        
        ax.plot(bcm[rv], pdf_r_m[rv], marker='o', linestyle='None', color='darkorange', linewidth=1.2, markersize=4, label=regcm_label)
        ax.plot(bcm[ev], pdf_e_m[ev], marker='s', linestyle='None', color='tab:blue', linewidth=1.2, markersize=4, label='ERA5 (~31 km)')
                
        ax.set_yscale('log')
        ax.set_xscale('log')
        ax.set_ylim(1e-6, 1.0)
        ax.set_xlim(0.1, 50)
        
        ax.set_xlabel('Precipitation Intensity (mm h⁻¹)', fontsize=12)
        ax.set_ylabel('Probability density', fontsize=12)
        ax.set_title(f'Hourly Precipitation PDF — {variant_name} ({title_period})', fontsize=12, fontweight='bold', pad=15)
        
        ax.legend(loc='upper right', frameon=True, fontsize=10)
        ax.grid(True, which='major', linestyle='--', alpha=0.5, color='#b0b0b0')
        ax.grid(False, which='minor')
        
        # Inset
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        axins = inset_axes(ax, width="35%", height="35%", loc='lower left', bbox_to_anchor=(0.1, 0.1, 1, 1), bbox_transform=ax.transAxes)
        
        rv_i = pdf_r_i > 0
        ev_i = pdf_e_i > 0
        
        axins.plot(bci[rv_i], pdf_r_i[rv_i], marker='o', linestyle='None', color='darkorange', linewidth=1, markersize=3)
        axins.plot(bci[ev_i], pdf_e_i[ev_i], marker='s', linestyle='None', color='tab:blue', linewidth=1, markersize=3)
                   
        axins.set_yscale('log')
        axins.set_xlim(0, 5)
        axins.set_ylim(1e-3, 1.0)
        axins.set_title('Low intensity', fontsize=10, fontweight='bold')
        axins.tick_params(axis='both', which='major', labelsize=8)
        axins.grid(True, which='major', linestyle='--', alpha=0.5, color='#b0b0b0')
        axins.grid(False, which='minor')
        
        fig_name = f"pr_hourly_pdf_{variant_name.replace(' ', '_').lower()}_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.png"
        fig_path = os.path.join(out_dir, fig_name)
        plt.savefig(fig_path)
        plt.close(fig)
        logger.info(f"Saved {fig_path}")

    # Total theoretical samples for normalization
    samples_r_nat = regcm_mask.sum() * regcm_total_valid_hours
    samples_e = era5_mask.sum() * era5_total_valid_hours
    # For aggregated RegCM, the theoretical sample space is the ERA5 grid
    samples_r_agg = era5_mask.sum() * regcm_total_valid_hours
    
    # 1. Native Grid Plot
    plot_pdf(regcm_nat_pooled, era5_pooled, "Native Resolution", "RegCM Native (~3km)", samples_r_nat, samples_e)
    
    # 2. Common Grid Plot
    plot_pdf(regcm_agg_pooled, era5_pooled, "Common Grid", "RegCM Aggregated (~31km)", samples_r_agg, samples_e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--region", type=str, default="Morocco")
    args = parser.parse_args()
    process_pdfs(args.start_date, args.end_date, args.region)
