# RegCM r3km — Postprocessing & Validation Framework

**Author**: M. El Aabaribaoune (@um6p)

Postprocesses the **r3km** climate simulation and evaluates model outputs against observational references (e.g., CHIRPS, CPC). This framework is highly dynamic and driven by YAML configuration files, allowing full control over variables, processing modules, and visualization settings without modifying the underlying Python code.

## Directory Architecture

```
postproc/
├── configs/
│   ├── default_eval.yaml       ← Edit paths, variables, and visual settings HERE
│   └── ...                     ← You can create as many config files as you need
├── src/
│   ├── config_parser.py        ← Parses the YAML and provides settings to the scripts
│   ├── run_all.sh              ← Master pipeline driver
│   ├── 00_check_data.py        ← Sanity checks for all inputs
│   ├── 01_preprocess.py        ← Time subsetting & unit conversions
│   ├── 02_regrid.py            ← Spatial regridding (obs ↔ model) via xESMF
│   ├── 03_climatology_maps.py  ← 2D annual and seasonal climatology maps
│   ├── 04_bias_maps.py         ← 2D spatial bias maps (Model − Observation)
│   ├── 05_seasonal_cycle.py    ← Area-averaged monthly cycle comparisons
│   ├── 06_taylor_diagram.py    ← Taylor diagrams for model performance
│   └── 07_metrics_table.py     ← Computes MB, RMSE, r, KGE (exports CSV/MD)
├── data/                       ← Intermediate NetCDFs (ignored by git)
└── results/
    ├── maps/                   ← PNG maps (climatology, bias)
    ├── timeseries/             ← PNG seasonal cycle plots
    ├── taylor/                 ← PNG Taylor diagrams
    └── tables/                 ← Metrics tables in CSV and Markdown
```

## Quick Start

The master script `run_all.sh` accepts a YAML configuration file as its first argument.

```bash
cd /path/to/r3km/postproc

# Run the pipeline with the default evaluation configuration
bash src/run_all.sh configs/default_eval.yaml

# Submit it as a SLURM batch job (runs in background on cluster)
sbatch job_postproc.sh
```

> **Note**: You can toggle specific modules (e.g., disable Taylor diagrams or regridding) directly inside the YAML file under the `modules:` section by setting them to `false`.

## Data Sources (Validation)

The current default evaluation relies on the subsetted reference data for the Morocco domain (`14N-42N, 32W-7E`):

| Variable | Model Output | Observational Reference |
|---|---|---|
| `pr` (Precipitation) | `T01/output/*_STS.*.nc` | CHIRPS (`data/CHIRPS/chirps_2000.nc`) |
| `tasmax` (Max Temp) | same | CPC Global (`data/CPC/tmax.2000.nc`) |
| `tasmin` (Min Temp) | same | CPC Global (`data/CPC/tmin.2000.nc`) |

## Dependencies

Required Python packages (available in the cluster's `Anaconda3` module):
```bash
pip install netCDF4 numpy matplotlib cartopy scipy pyyaml
pip install xesmf   # Required for robust spatial regridding
```

## Configuration (YAML)

All paths, modules, and visual parameters are centralized in `configs/*.yaml`.
- **`general`**: Defines the simulation period (`year_start` / `year_end`), simulation path, and domain bounding box.
- **`modules`**: Boolean flags (`true`/`false`) to toggle execution of specific Python scripts.
- **`visuals`**: Global plot settings (DPI, format).
- **`variables`**: Specific metadata for each variable, including input/output units, scale factors, colormaps (`cmap`, `cmap_bias`), and min/max limits (`vmin`, `vmax`).
