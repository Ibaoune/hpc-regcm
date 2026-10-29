#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
import sys, os, argparse, json, hashlib
from pathlib import Path
import netCDF4 as nc
import numpy as np
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import src.commun.config_parser as cp

try:
    import xesmf as xe
    import xarray as xr
    USE_XESMF = True
except ImportError:
    USE_XESMF = False
    from scipy.interpolate import RegularGridInterpolator

REGRIDDED_DIR = cp.DATA_DIR / "regridded"
REGRIDDED_DIR.mkdir(parents=True, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, default=cp.YEAR_START)
parser.add_argument("--vars", default=",".join(cp.VARIABLES))
parser.add_argument("--overwrite", action="store_true")
args = parser.parse_args()

YEAR = args.year
varlist = [v.strip() for v in args.vars.split(",")]

print(f"\n{'═'*60}")
print(f"  02_regrid — year {YEAR}  vars: {varlist}")
print(f"{'═'*60}")

def get_config_hash(cfg):
    cfg_str = json.dumps(cfg, sort_keys=True)
    return hashlib.md5(cfg_str.encode()).hexdigest()

def check_cache(meta_path, current_hash, force_overwrite):
    if force_overwrite or not meta_path.exists(): return False
    try:
        with open(meta_path, "r") as f:
            meta = json.load(f)
        if meta.get("config_hash") == current_hash:
            return True
    except: pass
    return False

def load_data(path, var, is_model=False):
    with nc.Dataset(path) as ds:
        if is_model:
            lat = np.asarray(ds.variables["xlat"][:], dtype=np.float32)
            lon = np.asarray(ds.variables["xlon"][:], dtype=np.float32)
            mask = ds.variables.get("mask", None)
            if mask is not None: mask = np.asarray(mask[:], dtype=np.float32)
        else:
            lat = np.asarray(ds.variables["lat"][:], dtype=np.float32)
            lon = np.asarray(ds.variables["lon"][:], dtype=np.float32)
            mask = None
        raw_data = ds.variables[var][:]
        if isinstance(raw_data, np.ma.MaskedArray):
            data = np.where(raw_data.mask, np.nan, raw_data.data)
        else:
            data = raw_data
        data = np.asarray(data, dtype=np.float32)
        t = ds.variables["time"][:]
        t_units = ds.variables["time"].units
        
        has_bounds = False
        if is_model and ("xlat_bnds" in ds.variables or "bounds" in getattr(ds.variables.get("xlat"), "ncattrs", lambda: [])()):
            has_bounds = True
        elif not is_model and ("lat_bnds" in ds.variables or "bounds" in getattr(ds.variables.get("lat"), "ncattrs", lambda: [])()):
            has_bounds = True
            
    return lat, lon, mask, data, t, t_units, has_bounds

def do_regrid(src_lat, src_lon, src_data, dst_lat, dst_lon, method, src_curvilinear, reuse_weights=True):
    if not USE_XESMF:
        if method == "conservative":
            print("       [WARNING] Scipy fallback doesn't support conservative. Using bilinear.")
        
        # Scipy fallback (requires strictly ascending coords)
        src_lat_1d = src_lat if src_lat.ndim == 1 else src_lat[:, 0]
        src_lon_1d = src_lon if src_lon.ndim == 1 else src_lon[0, :]
        
        if src_lat_1d[0] > src_lat_1d[-1]:
            src_lat_1d = src_lat_1d[::-1]
            src_data = src_data[:, ::-1, :]
            
        ntime = src_data.shape[0]
        dst_pts = np.column_stack([dst_lat.ravel(), dst_lon.ravel()])
        out = np.full((ntime, *dst_lat.shape), np.nan, dtype=np.float32)
        for i in range(ntime):
            rgi = RegularGridInterpolator((src_lat_1d, src_lon_1d), src_data[i], method="linear", bounds_error=False, fill_value=np.nan)
            out[i] = rgi(dst_pts).reshape(dst_lat.shape)
        return out

    # xESMF
    if src_curvilinear:
        ds_src = xr.Dataset({"lat": (["y","x"], src_lat), "lon": (["y","x"], src_lon)})
    else:
        lon2d, lat2d = np.meshgrid(src_lon, src_lat)
        ds_src = xr.Dataset({"lat": (["y","x"], lat2d), "lon": (["y","x"], lon2d)})
        
    if dst_lat.ndim == 1:
        dst_lon2d, dst_lat2d = np.meshgrid(dst_lon, dst_lat)
    else:
        dst_lat2d, dst_lon2d = dst_lat, dst_lon
        
    ds_dst = xr.Dataset({"lat": (["y","x"], dst_lat2d), "lon": (["y","x"], dst_lon2d)})
    
    weights_dir = cp.DATA_DIR / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)
    src_tag = f"{ds_src['lat'].shape[0]}x{ds_src['lat'].shape[1]}"
    dst_tag = f"{ds_dst['lat'].shape[0]}x{ds_dst['lat'].shape[1]}"
    weights_file = str(weights_dir / f"regrid_{method}_{src_tag}_to_{dst_tag}.nc")
    reuse = reuse_weights and os.path.exists(weights_file)
    regridder = xe.Regridder(ds_src, ds_dst, method, periodic=False, filename=weights_file, reuse_weights=reuse)
    
    ntime = src_data.shape[0]
    ny_dst, nx_dst = dst_lat2d.shape
    out = np.full((ntime, ny_dst, nx_dst), np.nan, dtype=np.float32)
    for i in range(ntime):
        sl = src_data[i]
        if isinstance(sl, np.ma.MaskedArray):
            sl = np.where(sl.mask, np.nan, sl.data)
        res = regridder(np.asarray(sl, dtype=np.float32))
        out[i] = res.values if hasattr(res, 'values') else res
    return out

def save_regridded(out_path, var, data, t_arr, t_units, lat, lon, curvilinear=False, extra_meta=""):
    with nc.Dataset(out_path, "w", format="NETCDF4") as ds:
        ntime = data.shape[0]
        if curvilinear:
            ny, nx = lat.shape
            ds.createDimension("time", ntime)
            ds.createDimension("iy", ny)
            ds.createDimension("jx", nx)
            dims = ("time", "iy", "jx")
        else:
            nlat, nlon = lat.shape[0], lon.shape[0]
            ds.createDimension("time", ntime)
            ds.createDimension("lat", nlat)
            ds.createDimension("lon", nlon)
            dims = ("time", "lat", "lon")
            
        t_out = ds.createVariable("time", "f8", ("time",))
        t_out.units = t_units
        t_out.calendar = "standard"
        t_out[:] = t_arr
        
        if curvilinear:
            vlat = ds.createVariable("xlat", "f4", ("iy","jx"))
            vlon = ds.createVariable("xlon", "f4", ("iy","jx"))
        else:
            vlat = ds.createVariable("lat", "f4", ("lat",))
            vlon = ds.createVariable("lon", "f4", ("lon",))
            
        vlat[:] = lat
        vlon[:] = lon
        
        vout = ds.createVariable(var, "f4", dims, zlib=True, complevel=4, fill_value=np.nan)
        vout.units = cp.MODEL[var]["units_out"]
        vout[:] = data
        ds.description = extra_meta
        ds.created_by = "02_regrid.py"

for var in varlist:
    print(f"\n  ── {var} ──────────────────────────────────────────────")
    for ref_name, obs_cfg in cp.OBS[var].items():
        if obs_cfg.get("type") == "stations":
            continue
            
        obs_ds_name = ref_name
        
        mod_path = cp.DATA_DIR / "processed" / "model" / var / f"{YEAR}.nc"
        obs_path = cp.DATA_DIR / "processed" / "obs" / obs_ds_name / var / f"{YEAR}.nc"
        
        if not mod_path.exists() or not obs_path.exists():
            print(f"       [WARNING] Missing preprocessed files for {var} {YEAR} ({obs_ds_name})")
            continue
            
        xlat, xlon, mask, mod_data, mod_t, mod_tunits, mod_bounds = load_data(mod_path, var, is_model=True)
        obs_lat, obs_lon, _, obs_data, obs_t, obs_tunits, obs_bounds = load_data(obs_path, var, is_model=False)

        for task_name, task_cfg in cp.REGRIDDING.items():
            if not isinstance(task_cfg, dict):
                continue
            direction = task_cfg.get("direction")
            methods = task_cfg.get("methods", {})
            method = methods.get(var, "bilinear")
            reuse = cp.REGRIDDING.get("reuse_weights", True)
            
            if direction not in ["MODEL_TO_OBS", "OBS_TO_MODEL"]:
                continue
                
            cfg_hash = get_config_hash({"direction": direction, "method": method, "var": var, "obs": obs_ds_name})
            
            is_obs_curv = (obs_lat.ndim == 2)
            
            if direction == "MODEL_TO_OBS":
                out_dir = REGRIDDED_DIR / obs_ds_name / "model" / var
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{YEAR}.nc"
                meta_path = out_dir / f"{YEAR}.meta.json"
                
                if check_cache(meta_path, cfg_hash, args.overwrite):
                    print(f"     [MODEL_TO_OBS] {var} -> Using cache ({obs_ds_name})")
                    continue
                    
                print(f"     [MODEL_TO_OBS] {var} ({method}) onto {obs_ds_name}...")
                if method == "conservative" and (not mod_bounds or not obs_bounds):
                    raise ValueError(f"Cell bounds missing for conservative on RegCM. Action=fail. Update YAML to bilinear for {var}.")
                    
                if is_obs_curv:
                    obs_lat2d_c = obs_lat
                    obs_lon2d_c = obs_lon
                else:
                    obs_lon2d_c, obs_lat2d_c = np.meshgrid(obs_lon, obs_lat)
                
                rg_data = do_regrid(xlat, xlon, mod_data, obs_lat2d_c, obs_lon2d_c, method, True, reuse)
                save_regridded(out_path, var, rg_data, mod_t, mod_tunits, obs_lat, obs_lon, is_obs_curv, f"RegCM {var} on {obs_ds_name} grid")
                
                with open(meta_path, "w") as f:
                    json.dump({"config_hash": cfg_hash, "method": method, "regrid_direction": "MODEL_TO_OBS", "weights_used": reuse}, f)
                    
            elif direction == "OBS_TO_MODEL":
                out_dir = REGRIDDED_DIR / "model" / obs_ds_name / var
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{YEAR}.nc"
                meta_path = out_dir / f"{YEAR}.meta.json"
                
                if check_cache(meta_path, cfg_hash, args.overwrite):
                    print(f"     [OBS_TO_MODEL] {var} -> Using cache ({obs_ds_name})")
                    continue
                    
                print(f"     [OBS_TO_MODEL] {var} ({method}) from {obs_ds_name}...")
                if method == "conservative" and (not obs_bounds or not mod_bounds):
                    raise ValueError(f"Cell bounds missing for conservative on RegCM. Action=fail. Update YAML to bilinear for {var}.")
                    
                rg_data = do_regrid(obs_lat, obs_lon, obs_data, xlat, xlon, method, is_obs_curv, reuse)
                
                # Apply mask to target
                for i in range(rg_data.shape[0]):
                    rg_data[i] = np.where(mask == 1, rg_data[i], np.nan)
                    
                save_regridded(out_path, var, rg_data, obs_t, obs_tunits, xlat, xlon, True, f"{obs_ds_name} {var} on RegCM grid")
                
                with open(meta_path, "w") as f:
                    json.dump({"config_hash": cfg_hash, "method": method, "regrid_direction": "OBS_TO_MODEL", "weights_used": reuse}, f)

print(f"\n{'═'*60}")
print(f"  ✔  Regridding complete for year {YEAR}")
print(f"{'═'*60}\n")
