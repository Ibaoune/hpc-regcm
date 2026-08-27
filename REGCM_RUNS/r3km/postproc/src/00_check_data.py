"""
00_check_data.py
================
Description: Validates the presence and integrity of observation and model data before processing.
Author: M. El Aabaribaoune (@um6p)
"""

#!/usr/bin/env python3
"""
00_check_data.py  –  Sanity check all model and observation input files.
=========================================================================
Usage:
    python3 src/00_check_data.py

Exit code 0 → all OK.
Exit code 1 → one or more files missing or unreadable.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_parser import *

import netCDF4 as nc
import numpy as np
from datetime import datetime, timedelta

OK     = "\033[32m✔\033[0m"
WARN   = "\033[33m⚠\033[0m"
FAIL   = "\033[31m✘\033[0m"
errors = []


def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


def check(cond, msg_ok, msg_fail):
    if cond:
        print(f"  {OK} {msg_ok}")
    else:
        print(f"  {FAIL} {msg_fail}")
        errors.append(msg_fail)


# ─── 1. Model STS files ──────────────────────────────────────────────────────
section(f"Model STS files — year {YEAR_START}")
files = sts_files(YEAR_START)
check(len(files) > 0, f"Found {len(files)} STS files for {YEAR_START}",
      f"No STS files found for {YEAR_START} in {OUTPUT_DIR}")

if files:
    # Expect 366 files for 2000 (leap year) or 365
    check(len(files) >= 365,
          f"File count {len(files)} ≥ 365 (looks complete)",
          f"Only {len(files)} STS files — simulation may not cover full year {YEAR_START}")

    # Peek at first file
    try:
        ds = nc.Dataset(files[0])
        for var in ["tasmax", "tasmin", "pr"]:
            check(var in ds.variables,
                  f"Variable '{var}' present in STS files",
                  f"Variable '{var}' MISSING from STS files")
            if var in ds.variables:
                v = ds.variables[var]
                print(f"       {var}: shape={v.shape}, units={getattr(v,'units','?')}")
        t = ds.variables["time"]
        print(f"       time: units={t.units}, val={float(t[0]):.1f}")
        xlat = ds.variables["xlat"][:]
        xlon = ds.variables["xlon"][:]
        print(f"       grid: lat [{xlat.min():.2f}, {xlat.max():.2f}]  lon [{xlon.min():.2f}, {xlon.max():.2f}]")
        ds.close()
    except Exception as e:
        errors.append(str(e))
        print(f"  {FAIL} Could not open {files[0].name}: {e}")

    # Peek at last file
    try:
        ds_last = nc.Dataset(files[-1])
        t_last = ds_last.variables["time"]
        print(f"       last file: {files[-1].name}  time={float(t_last[0]):.1f}")
        ds_last.close()
    except Exception as e:
        errors.append(str(e))
        print(f"  {FAIL} Could not open {files[-1].name}: {e}")


# ─── 2. MSWEP precipitation ──────────────────────────────────────────────────
section("Observation: MSWEP precipitation")
obs_cfg = OBS["pr"]
fpath = obs_cfg["path"]
check(fpath.exists(), f"File exists: {fpath.name}", f"MISSING: {fpath}")

if fpath.exists():
    try:
        ds = nc.Dataset(fpath)
        var = obs_cfg["var"]
        check(var in ds.variables,
              f"Variable '{var}' found",
              f"Variable '{var}' not found in {fpath.name}")
        t   = ds.variables["time"]
        lat = ds.variables[obs_cfg["lat_name"]][:]
        lon = ds.variables[obs_cfg["lon_name"]][:]
        pr  = ds.variables[var]
        print(f"       precipitation: shape={pr.shape}, units={getattr(pr,'units','?')}")
        print(f"       time: units={t.units}, shape={t.shape}")
        print(f"       lat [{lat.min():.2f}, {lat.max():.2f}]  lon [{lon.min():.2f}, {lon.max():.2f}]")

        # Check temporal overlap with YEAR_START
        from netCDF4 import num2date
        dates = num2date(t[:], t.units, calendar="proleptic_gregorian")
        years = np.array([d.year for d in dates])
        n_year = (years == YEAR_START).sum()
        check(n_year > 0,
              f"{n_year} time steps available for year {YEAR_START}",
              f"No time steps found for year {YEAR_START} in MSWEP!")
        ds.close()
    except Exception as e:
        errors.append(str(e))
        print(f"  {FAIL} Error reading MSWEP: {e}")


# ─── 3. CPC tasmax ───────────────────────────────────────────────────────────
for vname in ["tasmax", "tasmin"]:
    obs_cfg = OBS[vname]
    fpath   = obs_cfg["path"]
    section(f"Observation: CPC {vname}")
    check(fpath.exists(), f"File exists: {fpath.name}", f"MISSING: {fpath}")

    if fpath.exists():
        try:
            ds  = nc.Dataset(fpath)
            var = obs_cfg["var"]
            check(var in ds.variables,
                  f"Variable '{var}' found",
                  f"Variable '{var}' not found in {fpath.name}")
            t   = ds.variables["time"]
            lat = ds.variables["lat"][:]
            lon = ds.variables["lon"][:]
            v   = ds.variables[var]
            print(f"       {var}: shape={v.shape}, units={getattr(v,'units','?')}")
            print(f"       time: units={t.units}, shape={t.shape}")
            print(f"       lat [{lat.min():.2f}, {lat.max():.2f}]  lon [{lon.min():.2f}, {lon.max():.2f}]")

            from netCDF4 import num2date
            dates = num2date(t[:], t.units, calendar="proleptic_gregorian")
            years = np.array([d.year for d in dates])
            n_year = (years == YEAR_START).sum()
            check(n_year > 0,
                  f"{n_year} time steps available for year {YEAR_START}",
                  f"No time steps for year {YEAR_START} in CPC {vname}!")
            ds.close()
        except Exception as e:
            errors.append(str(e))
            print(f"  {FAIL} Error reading CPC {vname}: {e}")


# ─── 4. Python environment ───────────────────────────────────────────────────
section("Python environment")
for pkg in ["netCDF4", "numpy", "matplotlib", "cartopy", "scipy"]:
    try:
        __import__(pkg.replace("-","_"))
        print(f"  {OK} {pkg}")
    except ImportError:
        print(f"  {WARN} {pkg} not found (optional for some scripts)")

for pkg in ["xesmf"]:
    try:
        __import__(pkg)
        print(f"  {OK} {pkg} (fast regridding available)")
    except ImportError:
        print(f"  {WARN} {pkg} not installed — scipy fallback will be used")


# ─── Summary ─────────────────────────────────────────────────────────────────
print(f"\n{'═'*60}")
if errors:
    print(f"  {FAIL} CHECK FAILED — {len(errors)} error(s):")
    for e in errors:
        print(f"       • {e}")
    sys.exit(1)
else:
    print(f"  {OK} ALL CHECKS PASSED — ready to preprocess year {YEAR_START}")
print(f"{'═'*60}\n")
