#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
import sys, os, argparse, json, hashlib
from pathlib import Path
import netCDF4 as nc
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import src.commun.config_parser as cp

# directories
PROCESSED_DIR = cp.DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, default=cp.YEAR_START)
parser.add_argument("--vars", default=",".join(cp.VARIABLES))
parser.add_argument("--overwrite", action="store_true", help="Force overwrite cache")
args = parser.parse_args()

YEAR = args.year
varlist = [v.strip() for v in args.vars.split(",")]

print(f"\n{'═'*60}")
print(f"  01_preprocess — year {YEAR}  vars: {varlist}")
print(f"{'═'*60}")

def cf_to_datetimes(t_var):
    import cftime
    return cftime.num2date(t_var[:], t_var.units, calendar=getattr(t_var, "calendar", "standard"))

def get_config_hash(cfg):
    cfg_str = json.dumps(cfg, sort_keys=True)
    return hashlib.md5(cfg_str.encode()).hexdigest()

def check_cache(meta_path, current_hash, force_overwrite):
    if force_overwrite or not meta_path.exists():
        return False
    try:
        with open(meta_path, "r") as f:
            meta = json.load(f)
        if meta.get("config_hash") == current_hash:
            return True
    except:
        pass
    return False

def apply_sanity_checks(var_name, data, cfg, dataset_name):
    vmin = cfg.get("valid_min")
    vmax = cfg.get("valid_max")
    action = cfg.get("action", "warn")
    
    msg = []
    if vmin is not None and np.nanmin(data) < vmin:
        msg.append(f"Min value {np.nanmin(data):.4f} < {vmin}")
    if vmax is not None and np.nanmax(data) > vmax:
        msg.append(f"Max value {np.nanmax(data):.4f} > {vmax}")
        
    if msg:
        full_msg = f"Sanity check failed for {var_name} in {dataset_name}: " + " | ".join(msg)
        if action == "fail":
            raise ValueError(full_msg)
        else:
            print(f"       [WARNING] {full_msg}")
    return data

def process_model(var: str, year: int, force: bool):
    cfg = cp.MODEL[var]
    current_hash = get_config_hash(cfg)
    
    out_dir = PROCESSED_DIR / "model" / var
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{year}.nc"
    meta_path = out_dir / f"{year}.meta.json"
    
    if check_cache(meta_path, current_hash, force):
        print(f"  [MODEL] {var} ({year}) -> Using valid cache")
        return out_path
        
    stream = cfg.get("stream", "STS")
    import glob
    files = sorted(glob.glob(f"{cp.OUTPUT_DIR}/*_{stream}.{year}*.nc"))
    if not files:
        archive_dir = cp.OUTPUT_DIR.parent / "archive_periods" / f"{year}_all"
        files = sorted(glob.glob(f"{archive_dir}/*_{stream}.{year}*.nc"))
    if not files:
        raise FileNotFoundError(f"No RegCM {stream} files found for year {year}")
        
    print(f"\n  [MODEL] {var}  ({len(files)} files)")

    with nc.Dataset(files[0]) as ds0:
        xlat = ds0.variables["xlat"][:]
        xlon = ds0.variables["xlon"][:]
        mask = ds0.variables["mask"][:]
        topo = ds0.variables["topo"][:]
        ny, nx = xlat.shape
        t0_var = ds0.variables["time"]
        dt_objs = cf_to_datetimes(t0_var)
        if len(dt_objs) > 1:
            dt_sec = (dt_objs[1] - dt_objs[0]).total_seconds()
        else:
            # STS has exactly 1 record per file = one daily mean
            # The correct accumulation period is 86400s, NOT 3600s
            dt_sec = 86400.0

    is_rate = cfg.get("is_rate", False)
    
    daily_data = []
    daily_times = []
    
    for i, fpath in enumerate(files):
        try:
            with nc.Dataset(fpath) as ds:
                raw = ds.variables[cfg["var"]][:].squeeze()
                if hasattr(raw, "mask"):
                    raw = np.where(raw.mask, np.nan, raw.data)
                    
                raw = raw.astype(np.float32)
                
                # rate to accumulation
                if is_rate:
                    raw = raw * dt_sec
                    
                # scale and offset
                scale = cfg.get("scale", 1.0)
                offset = cfg.get("offset", 0.0)
                val = (raw * scale) + offset
                
                # RegCM files might be sub-daily, so we must accumulate/average to daily
                t_var = ds.variables["time"]
                dts = cf_to_datetimes(t_var)
                
                # Simple daily grouping assuming file boundaries align roughly with days
                # If a file has multiple steps, we mean or sum them
                if is_rate:
                    daily_val = np.nansum(val, axis=0) if val.ndim == 3 else val
                else:
                    daily_val = np.nanmean(val, axis=0) if val.ndim == 3 else val
                    
                daily_data.append(daily_val)
                daily_times.append(dts[0])
        except Exception as e:
            print(f"       [WARNING] Skipping corrupt file {fpath}: {e}")
            continue

    data = np.stack(daily_data)
    data = apply_sanity_checks(var, data, cfg, "RegCM-r3km")

    # save
    with nc.Dataset(out_path, "w", format="NETCDF4") as out:
        out.createDimension("time", len(daily_times))
        out.createDimension("iy", ny)
        out.createDimension("jx", nx)

        t_out = out.createVariable("time", "f8", ("time",))
        t_out.units = f"days since {year}-01-01 00:00:00"
        t_out.calendar = "standard"
        ref = datetime(year, 1, 1)
        t_out[:] = np.array([(datetime(d.year, d.month, d.day) - ref).days for d in daily_times])

        vlat = out.createVariable("xlat", "f4", ("iy", "jx"))
        vlat[:] = xlat
        vlon = out.createVariable("xlon", "f4", ("iy", "jx"))
        vlon[:] = xlon

        vmask = out.createVariable("mask", "f4", ("iy", "jx"))
        vmask[:] = mask

        vout = out.createVariable(var, "f4", ("time", "iy", "jx"), zlib=True, complevel=4, fill_value=np.nan)
        vout.units = cfg["units_out"]
        
        if is_rate:
            vout.source_standard_name = "precipitation_flux"
            vout.source_units = "kg m-2 s-1"
            vout.source_cell_methods = "time: mean"
            vout.conversion_applied = "amount = mean_rate * timestep_seconds"
            vout.timestep_seconds = dt_sec
            vout.standard_name = "lwe_thickness_of_precipitation_amount"
            vout.cell_methods = "time: sum"
            
        vout[:] = data

    # compute robust fingerprint
    import hashlib
    fp_str = ""
    for f in sorted(files):
        sz = os.path.getsize(f)
        mt = os.path.getmtime(f)
        fp_str += f"{os.path.basename(f)}|{sz}|{mt}||"
    source_fp = hashlib.md5(fp_str.encode()).hexdigest()
    
    total_size = sum(os.path.getsize(f) for f in files)
    latest_mtime = max(os.path.getmtime(f) for f in files)
    
    # save meta
    meta = {
        "config_hash": current_hash,
        "variable": var,
        "period": year,
        "source": "RegCM",
        "created_at": datetime.now().isoformat(),
        "source_fingerprint": source_fp,
        "source_file_count": len(files),
        "source_first_file": os.path.basename(str(files[0])),
        "source_last_file": os.path.basename(str(files[-1])),
        "source_latest_mtime": float(latest_mtime),
        "source_total_size": int(total_size)
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"       ✔ {out_path.name}  shape={data.shape}")
    return out_path

def process_obs(var: str, year: int, force: bool):
    model_cfg = cp.MODEL[var]
    print(f"\n  [OBS] {var} ({year})")
    for ref_name, obs_cfg in cp.OBS[var].items():
        if obs_cfg.get("type") == "stations":
            continue
            
        current_hash = get_config_hash(obs_cfg)
        dataset_name = ref_name
        path_template = obs_cfg["path_template"]
        fpath_str = path_template.format(year=year, var=obs_cfg["var"])
        
        actual_fpath = None
        if os.path.exists(fpath_str):
            actual_fpath = fpath_str
        elif "*" in fpath_str:
            import glob, re
            cands = sorted(glob.glob(fpath_str))
            for c in cands:
                m = re.search(r"_(\d{4})\d{4}-(\d{4})\d{4}\.nc", c)
                if m:
                    sy, ey = int(m.group(1)), int(m.group(2))
                    if sy <= year <= ey:
                        actual_fpath = c
                        break
            if actual_fpath is None and len(cands) > 0:
                import cftime
                for c in cands:
                    try:
                        with nc.Dataset(c) as dsc:
                            tv = dsc.variables.get(cp.cfg.get("datasets", {}).get(dataset_name, {}).get("time_name", "time"))
                            if tv is not None:
                                dts_c = cftime.num2date(tv[:], tv.units, calendar=getattr(tv, "calendar", "standard"))
                                if any(d.year == year for d in dts_c):
                                    actual_fpath = c
                                    break
                    except:
                        pass
                        
        if actual_fpath is None:
            print(f"       ⚠ {dataset_name} file not found: {fpath_str}")
            continue
            
        fpath_str = actual_fpath
            
        out_dir = PROCESSED_DIR / "obs" / dataset_name / var
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{year}.nc"
        meta_path = out_dir / f"{year}.meta.json"
        
        if check_cache(meta_path, current_hash, force):
            print(f"       [CACHE HIT] {dataset_name}")
            continue
            
        print(f"       → Processing {dataset_name} from {os.path.basename(fpath_str)}")
        try:
            with nc.Dataset(fpath_str) as ds:
                time_var = ds.variables.get(cp.cfg.get("datasets", {}).get(dataset_name, {}).get("time_name", "time"))
                if time_var is None:
                    print(f"       ⚠ Cannot find time variable for {dataset_name}")
                    continue
                t_data_full = time_var[:]
                t_units = time_var.units
                
                # Subset by year
                import cftime
                dts = cftime.num2date(t_data_full, t_units, calendar=getattr(time_var, "calendar", "standard"))
                mask = np.array([d.year == year for d in dts])
                
                if mask.sum() == 0:
                    print(f"       ⚠ No data found for year {year} in {dataset_name}")
                    continue
                    
                time_idx = np.where(mask)[0]
                raw_var = ds.variables[obs_cfg["var"]]
                data = raw_var[time_idx]
                t_data = t_data_full[mask]
                
                # Squeeze extraneous dims if necessary (e.g. depth=1)
                if data.ndim == 4 and data.shape[1] == 1:
                    data = data.squeeze(axis=1)
                
                if np.ma.is_masked(data):
                    data = np.where(data.mask, np.nan, data.data)
                
                # Check for extreme fill values
                fill_val = float(cp.cfg.get("datasets", {}).get(dataset_name, {}).get("fill_val", -9999.0))
                if fill_val < 0:
                    data = np.where(data <= fill_val, np.nan, data)
                else:
                    data = np.where(data >= fill_val * 0.999, np.nan, data)
                data = np.where(data >= 1.0e15, np.nan, data)
                
                lat_var = ds.variables.get(cp.cfg.get("datasets", {}).get(dataset_name, {}).get("lat_name", "lat"))
                lon_var = ds.variables.get(cp.cfg.get("datasets", {}).get(dataset_name, {}).get("lon_name", "lon"))
                
                if lat_var is None or lon_var is None:
                    print(f"       ⚠ Cannot find lat/lon for {dataset_name}")
                    continue
                    
                lat = lat_var[:]
                lon = lon_var[:]
                
                # Automatic unit conversion:
                raw_units = getattr(raw_var, "units", "")
                if (var == "pr" and raw_units == "kg m-2 s-1") or obs_cfg.get("is_rate", False):
                    data = data * 86400.0
                    print(f"       [CONVERT] {var} multiplied by 86400 (kg m-2 s-1 → mm/day)")
                elif var in ["tasmax", "tasmin", "tas"] and (raw_units == "K" or np.nanmean(data) > 150.0):
                    data = data - 273.15
                    print(f"       [CONVERT] {var} converted from Kelvin to degC (- 273.15)")
                
            # Apply valid min/max logic from YAML (ONLY WARN/FAIL, NEVER CLIP)
            data = data.astype(np.float32)
            data = apply_sanity_checks(var, data, model_cfg, dataset_name)
            
            # --- Write Output ---
            with nc.Dataset(out_path, "w", format="NETCDF4") as out:
                out.createDimension("time", len(t_data))
                
                if lat.ndim == 1:
                    out.createDimension("lat", len(lat))
                    out.createDimension("lon", len(lon))
                    vlat = out.createVariable("lat", "f4", ("lat",))
                    vlon = out.createVariable("lon", "f4", ("lon",))
                else:
                    out.createDimension("iy", lat.shape[0])
                    out.createDimension("jx", lat.shape[1])
                    vlat = out.createVariable("lat", "f4", ("iy", "jx"))
                    vlon = out.createVariable("lon", "f4", ("iy", "jx"))
                    
                vlat[:] = lat
                vlon[:] = lon
                
                vt = out.createVariable("time", "f8", ("time",))
                vt.units = t_units
                vt[:] = t_data
                
                if lat.ndim == 1:
                    vout = out.createVariable(var, "f4", ("time", "lat", "lon"), zlib=True, fill_value=np.nan)
                else:
                    vout = out.createVariable(var, "f4", ("time", "iy", "jx"), zlib=True, fill_value=np.nan)
                    
                vout.units = model_cfg.get("units_out", "")
                vout[:] = data
                
            f_size = os.path.getsize(fpath_str)
            f_mtime = os.path.getmtime(fpath_str)
            import hashlib
            fp_str = f"{os.path.basename(fpath_str)}|{f_size}|{f_mtime}||"
            source_fp = hashlib.md5(fp_str.encode()).hexdigest()
            
            meta = {
                "config_hash": current_hash,
                "variable": var,
                "period": year,
                "source": dataset_name,
                "created_at": datetime.now().isoformat(),
                "source_fingerprint": source_fp,
                "source_file_count": 1,
                "source_first_file": os.path.basename(fpath_str),
                "source_last_file": os.path.basename(fpath_str),
                "source_latest_mtime": f_mtime,
                "source_total_size": f_size
            }
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2)
                
            print(f"       ✔ {out_path.name}  shape={data.shape}")
            
        except Exception as e:
            print(f"       ⚠ Error processing {dataset_name}: {e}")

if __name__ == "__main__":
    for var in varlist:
        process_model(var, YEAR, args.overwrite)
        process_obs(var, YEAR, args.overwrite)
    print(f"\n{'═'*60}")
    print(f"  ✔  Preprocessing complete for year {YEAR}")
    print(f"{'═'*60}\n")
