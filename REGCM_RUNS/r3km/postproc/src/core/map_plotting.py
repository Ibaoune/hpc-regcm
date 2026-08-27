# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
"""
map_plotting.py
===============
Centralized mapping utilities using Cartopy and Matplotlib.
Provides geographic contexts, QA logging, dynamic coordinate extents,
discrete colorbars from YAML, and sidecar JSON metadata generation.
"""

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import json
import csv
from pathlib import Path
from datetime import datetime

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False

def get_geographic_extent(lon_arr, lat_arr, lon_ref=None, lat_ref=None, buffer_deg=0.75):
    """
    Computes a tight bounding box around the data arrays plus a buffer.
    If reference arrays (e.g. MSWEP, CPC) are provided, computes the 
    intersection/common overlap between the two grids.
    """
    lmin, lmax = np.nanmin(lon_arr), np.nanmax(lon_arr)
    tmin, tmax = np.nanmin(lat_arr), np.nanmax(lat_arr)
    
    if lon_ref is not None and lat_ref is not None:
        rlmin, rlmax = np.nanmin(lon_ref), np.nanmax(lon_ref)
        rtmin, rtmax = np.nanmin(lat_ref), np.nanmax(lat_ref)
        
        # Intersection
        lmin = max(lmin, rlmin)
        lmax = min(lmax, rlmax)
        tmin = max(tmin, rtmin)
        tmax = min(tmax, rtmax)
    
    # In case there's no intersection or bounds are corrupted
    if lmin >= lmax or tmin >= tmax:
        return None
        
    return [float(lmin - buffer_deg), float(lmax + buffer_deg), float(tmin - buffer_deg), float(tmax + buffer_deg)]


def prepare_map_axis(ax, extent=None, plotting_cfg=None):
    """
    Applies Cartopy features and sets geographic extents based on plotting.yaml configurations.
    """
    if not HAS_CARTOPY:
        return
        
    if plotting_cfg is None:
        plotting_cfg = {}
        
    map_cfg = plotting_cfg.get("maps", {})
    
    if extent:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
    
    # Background
    bg = map_cfg.get("background", "neutral")
    if bg == "neutral":
        ax.set_facecolor('#F0F0F0') # Light gray
        ax.add_feature(cfeature.OCEAN, facecolor='#E8E8E8')
    else:
        ax.add_feature(cfeature.OCEAN)
        
    # Coastlines
    if map_cfg.get("coastlines", {}).get("enabled", True):
        lw = map_cfg.get("coastlines", {}).get("linewidth", 0.7)
        ax.add_feature(cfeature.COASTLINE, linewidth=lw)
        
    # Borders
    if map_cfg.get("borders", {}).get("enabled", True):
        lw = map_cfg.get("borders", {}).get("linewidth", 0.5)
        ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=lw, edgecolor='gray')
        
    # Gridlines
    if map_cfg.get("gridlines", {}).get("enabled", True):
        ls = map_cfg.get("gridlines", {}).get("linestyle", ":")
        lw = map_cfg.get("gridlines", {}).get("linewidth", 0.3)
        alpha = map_cfg.get("gridlines", {}).get("alpha", 0.5)
        gl = ax.gridlines(draw_labels=True, linewidth=lw, color='gray', alpha=alpha, linestyle=ls)
        if hasattr(gl, "top_labels"):
            gl.top_labels = False
            gl.right_labels = False
        else:
            gl.xlabels_top = False
            gl.ylabels_right = False


def plot_qa_check(figure_name, var_name, data, lon, lat, reference="None", period="Unknown"):
    """
    Runs automated QA checks prior to rendering a field. 
    Raises ValueError if the field is entirely invalid/empty.
    Logs metrics to results/qa/plot_qa.csv.
    """
    finite_mask = np.isfinite(data)
    finite_count = np.sum(finite_mask)
    total_cells = data.size
    finite_fraction = finite_count / total_cells if total_cells > 0 else 0
    
    if finite_count > 0:
        dmin = np.nanmin(data)
        dmax = np.nanmax(data)
        dmean = np.nanmean(data)
    else:
        dmin = dmax = dmean = np.nan
        
    qa_dir = Path("results/qa")
    qa_dir.mkdir(parents=True, exist_ok=True)
    qa_file = qa_dir / "plot_qa.csv"
    
    write_header = not qa_file.exists()
    
    status = "PASS" if finite_fraction > 0 else "FAIL"
    
    with open(qa_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "figure", "variable", "reference", "period", 
                             "status", "finite_fraction", "min", "mean", "max"])
        writer.writerow([datetime.utcnow().isoformat(), figure_name, var_name, reference, period,
                         status, f"{finite_fraction:.4f}", dmin, dmean, dmax])
                         
    if finite_fraction == 0:
        raise ValueError(f"[PLOT QA FAIL] Data for {figure_name} ({var_name} {period}) is entirely empty/NaN.")
        
    return True


def get_colormap_norm(var_name, is_bias, plotting_cfg):
    """
    Generates Matplotlib Colormap and Norm (Discrete BoundaryNorm) based on plotting.yaml.
    """
    var_cfg = plotting_cfg.get("variables", {}).get(var_name, {})
    
    if is_bias:
        cmap_name = var_cfg.get("cmap_bias", "RdBu_r")
        cfg = var_cfg.get("bias", {})
    else:
        cmap_name = var_cfg.get("cmap", "viridis")
        cfg = var_cfg.get("climatology", {})
        
    cmap = plt.get_cmap(cmap_name)
    
    if cfg.get("type") == "discrete" and "levels" in cfg:
        levels = cfg["levels"]
        norm = mcolors.BoundaryNorm(levels, ncolors=cmap.N)
        extend = cfg.get("extend", "both")
        return cmap, norm, levels, extend
    else:
        vmin = cfg.get("vmin", None)
        vmax = cfg.get("vmax", None)
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        return cmap, norm, None, "neither"


def save_figure_with_metadata(fig, out_path, metadata):
    """
    Saves a Matplotlib figure and writes an accompanying .meta.json sidecar file.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    metadata["created_at"] = datetime.utcnow().isoformat()
    metadata["figure"] = out_path.name
    
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    
    meta_path = out_path.with_suffix(".meta.json")
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=4)
