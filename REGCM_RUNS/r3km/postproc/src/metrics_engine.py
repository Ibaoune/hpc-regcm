# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
"""
metrics_engine.py
=================
Description: Core engine for area-weighted spatial and temporal metrics.
"""

import numpy as np

def compute_spatial_metrics(obs, mod, lat, lon, mask=None, cell_areas=None, use_coslat_fallback=True):
    """
    Compute area-weighted spatial metrics between model and obs fields.
    Both must be on the same grid.
    
    Args:
        obs, mod: 2D arrays (ny, nx)
        lat, lon: 2D arrays (ny, nx) or 1D
        mask: 2D boolean array (True where valid/inside evaluation region)
        cell_areas: 2D array of true cell areas.
        use_coslat_fallback: if True and cell_areas is None, use cos(lat) weighting.
        
    Returns:
        Dictionary of metrics: MB, MAE, RMSE, r, std_m, std_o, cov, n_valid
    """
    valid = np.isfinite(obs) & np.isfinite(mod)
    if mask is not None:
        valid = valid & mask
        
    if valid.sum() < 5:
        return {"n_valid": valid.sum(), "MB": np.nan, "MAE": np.nan, "RMSE": np.nan, 
                "r": np.nan, "std_m": np.nan, "std_o": np.nan, "cov": np.nan}
                
    o = obs[valid]
    m = mod[valid]
    
    if cell_areas is not None:
        w = cell_areas[valid]
    elif use_coslat_fallback:
        if lat.ndim == 1:
            lat2d = np.tile(lat[:, np.newaxis], (1, len(lon)))
            w = np.cos(np.deg2rad(lat2d))[valid]
        else:
            w = np.cos(np.deg2rad(lat))[valid]
    else:
        w = np.ones_like(o)
        
    # Ensure weights are valid and normalized
    w = np.clip(w, 0, None)
    W = w.sum()
    if W <= 0:
        return {"n_valid": valid.sum(), "MB": np.nan, "MAE": np.nan, "RMSE": np.nan, 
                "r": np.nan, "std_m": np.nan, "std_o": np.nan, "cov": np.nan}
        
    # Weighted Means
    mu_o = np.sum(o * w) / W
    mu_m = np.sum(m * w) / W
    
    # Bias
    diff = m - o
    mb = np.sum(diff * w) / W
    mae = np.sum(np.abs(diff) * w) / W
    rmse = np.sqrt(np.sum((diff**2) * w) / W)
    
    # Weighted Variance and Covariance
    var_o = np.sum(w * (o - mu_o)**2) / W
    var_m = np.sum(w * (m - mu_m)**2) / W
    cov = np.sum(w * (o - mu_o) * (m - mu_m)) / W
    
    std_o = np.sqrt(var_o)
    std_m = np.sqrt(var_m)
    
    if std_o > 0 and std_m > 0:
        r = cov / (std_o * std_m)
    else:
        r = np.nan
        
    return {
        "n_valid": valid.sum(),
        "MB": mb,
        "MAE": mae,
        "RMSE": rmse,
        "std_m": std_m,
        "std_o": std_o,
        "cov": cov,
        "r": r
    }

def compute_temporal_metrics(obs_ts, mod_ts):
    """
    Compute unweighted temporal metrics on time series.
    """
    valid = np.isfinite(obs_ts) & np.isfinite(mod_ts)
    if valid.sum() < 5:
        return {"n_valid": valid.sum(), "MB": np.nan, "MAE": np.nan, "RMSE": np.nan, "r": np.nan, "KGE": np.nan}
        
    o = obs_ts[valid]
    m = mod_ts[valid]
    
    mu_o = o.mean()
    mu_m = m.mean()
    
    diff = m - o
    mb = diff.mean()
    mae = np.abs(diff).mean()
    rmse = np.sqrt((diff**2).mean())
    
    sig_o = o.std()
    sig_m = m.std()
    
    r = np.corrcoef(o, m)[0, 1] if sig_o > 0 and sig_m > 0 else np.nan
    
    # KGE
    kge = np.nan
    if mu_o != 0 and sig_o != 0 and not np.isnan(r):
        beta = mu_m / mu_o
        alpha = sig_m / sig_o
        kge = 1 - np.sqrt((r - 1)**2 + (alpha - 1)**2 + (beta - 1)**2)
        
    return {
        "n_valid": valid.sum(),
        "MB": mb,
        "MAE": mae,
        "RMSE": rmse,
        "r": r,
        "KGE": kge
    }
