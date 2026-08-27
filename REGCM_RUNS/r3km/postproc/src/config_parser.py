# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
import os
import sys
from pathlib import Path
import yaml

config_path = os.environ.get("POSTPROC_CONFIG", None)

if not config_path:
    default_path = Path(__file__).resolve().parents[1] / "configs" / "default_eval.yaml"
    if default_path.exists():
        config_path = str(default_path)
    else:
        raise ValueError("POSTPROC_CONFIG environment variable is not set and default_eval.yaml not found.")

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

cfg = load_yaml(config_path)

import json
import hashlib

def get_config_hash():
    cfg_str = json.dumps(cfg, sort_keys=True)
    return hashlib.md5(cfg_str.encode()).hexdigest()

# Handle imports (New modular architecture)
if "imports" in cfg:
    base_dir = Path(config_path).parent
    for imp in cfg["imports"]:
        imp_path = base_dir / imp
        imp_cfg = load_yaml(imp_path)
        if imp_cfg:
            cfg.update(imp_cfg)

# --- General ---
# Legacy format uses 'general', new uses 'experiment', 'period', 'domain'
gen = cfg.get("general", {})
exp = cfg.get("experiment", {})
per = cfg.get("period", {})

_sim_root_str = exp.get("sim_root", gen.get("sim_root", "../../"))
SIM_ROOT = (Path(__file__).resolve().parent / _sim_root_str).resolve()
SIM_NAME = exp.get("sim_name", gen.get("sim_name", "T01"))
OUTPUT_DIR = SIM_ROOT / SIM_NAME / "output"

POSTPROC_ROOT = SIM_ROOT / "postproc"
DATA_DIR = POSTPROC_ROOT / "data"
RESULTS_DIR = POSTPROC_ROOT / "results"
MAPS_DIR = RESULTS_DIR / "maps"
TS_DIR = RESULTS_DIR / "timeseries"
TAYLOR_DIR = RESULTS_DIR / "taylor"
TABLES_DIR = RESULTS_DIR / "tables"

# Period logic
if "spinup" in per:
    SPINUP_YEAR = int(per["spinup"]["start"][:4])
else:
    SPINUP_YEAR = gen.get("spinup_year", 1999)

if "evaluation" in per:
    YEAR_START = int(per["evaluation"]["start"][:4])
    END_EVAL = per["evaluation"]["end"]
    if END_EVAL == "auto":
        # For auto, we will just set a default and let monitor or scripts handle it
        YEAR_END = 2004 # Placeholder if auto used outside monitor
    else:
        YEAR_END = int(END_EVAL[:4])
else:
    YEAR_START = gen.get("year_start", 2000)
    YEAR_END = gen.get("year_end", 2000)

DATE_START = f"{YEAR_START}0101"
DATE_END = f"{YEAR_END}1231"

# Domain / Regions
if "regions" in cfg:
    bbox = cfg["regions"]["morocco"]["bbox"]
else:
    bbox = gen.get("domain_bbox", [-18.0, 1.5, 21.0, 36.5])
DOMAIN_BBOX = dict(lon_min=bbox[0], lon_max=bbox[1], lat_min=bbox[2], lat_max=bbox[3])

SEASONS = gen.get("seasons", {
    "DJF": [12, 1, 2],
    "MAM": [3, 4, 5],
    "JJA": [6, 7, 8],
    "SON": [9, 10, 11]
})

# --- Visuals / Plotting ---
vis = cfg.get("visuals", {})
if "plotting" in cfg:
    plot_vis = cfg["plotting"].get("visuals", {})
    FIG_DPI = plot_vis.get("dpi", 150)
    FIG_EXT = plot_vis.get("format", "png")
else:
    FIG_DPI = vis.get("dpi", 150)
    FIG_EXT = vis.get("format", "png")

# --- Variables ---
VARIABLES = []
OBS = {}
MODEL = {}

var_dict = cfg.get("variables", {})

for var_key, var_cfg in var_dict.items():
    if not var_cfg.get("active", False):
        continue
        
    VARIABLES.append(var_key)
    
    # Legacy vs New format
    if "obs" in var_cfg: # Legacy
        o_cfg = var_cfg.get("obs", {})
        m_cfg = var_cfg.get("model", {})
        v_cfg = var_cfg.get("visuals", {})
        
        obs_raw_path = o_cfg.get("path")
        resolved_obs_path = (Path(config_path).resolve().parent / obs_raw_path).resolve()
        
        OBS[var_key] = {
            "path": resolved_obs_path,
            "var": o_cfg.get("var"),
            "label": o_cfg.get("label")
        }
        
        MODEL[var_key] = {
            "stream": m_cfg.get("stream"),
            "var": m_cfg.get("var"),
            "units_in": m_cfg.get("units_in"),
            "units_out": m_cfg.get("units_out"),
            "scale": m_cfg.get("scale", 1.0),
            "offset": m_cfg.get("offset", 0.0),
            "is_rate": (var_key == "pr"),
            "long_name": m_cfg.get("long_name"),
            "cmap": v_cfg.get("cmap", "viridis"),
            "cmap_bias": v_cfg.get("cmap_bias", "RdBu_r")
        }
    else: # New format
        ds_cat = cfg.get("datasets", {})
        refs = var_cfg.get("references", {})
        primary = refs.get("primary")
        secondary = refs.get("secondary", [])
        stations = refs.get("stations", [])
        
        OBS[var_key] = {}
        
        all_refs = [primary] + secondary + stations
        for ref in all_refs:
            if not ref: continue
            ds_info = ds_cat.get(ref, {})
            path_template = ds_info.get("path", "")
            if not path_template: continue
            
            if "{" in path_template:
                resolved_path = str((Path(config_path).resolve().parent / path_template).resolve())
            else:
                # Absolute or relative without format string
                p = Path(path_template)
                resolved_path = str(p if p.is_absolute() else (Path(config_path).resolve().parent / p).resolve())
            
            # Using same var name for obs as RegCM for now, or use defaults
            obs_var = var_key if ds_info.get("type") != "stations" else "Precipitation"
            if ref == "CHIRPS": obs_var = "precip"
            elif ref == "MSWEP": obs_var = "precipitation"
            
            OBS[var_key][ref] = {
                "path_template": resolved_path,
                "var": obs_var,
                "label": ds_info.get("label", ref),
                "type": ds_info.get("type", "obs")
            }
        
        # Merge plotting config for variable
        plot_var_cfg = cfg.get("plotting", {}).get("variables", {}).get(var_key, {})
        
        MODEL[var_key] = {
            "var": var_key,
            "units_in": var_cfg.get("units_in"),
            "units_out": var_cfg.get("units_out"),
            "scale": var_cfg.get("scale", 1.0),
            "offset": var_cfg.get("offset", 0.0),
            "is_rate": var_cfg.get("is_rate", False),
            "valid_min": var_cfg.get("valid_min"),
            "valid_max": var_cfg.get("valid_max"),
            "action": var_cfg.get("action", "warn"),
            "long_name": var_cfg.get("long_name"),
            "cmap": plot_var_cfg.get("cmap", "viridis"),
            "cmap_bias": plot_var_cfg.get("cmap_bias", "RdBu_r")
        }

MODULES = cfg.get("modules", {})
REGRIDDING = cfg.get("regridding", {})
