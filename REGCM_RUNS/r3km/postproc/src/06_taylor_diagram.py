"""
06_taylor_diagram.py
====================
Description: Generates Taylor diagrams to evaluate model performance (correlation, standard deviation).
Author: M. El Aabaribaoune (@um6p)
"""

#!/usr/bin/env python3
"""
06_taylor_diagram.py  –  Taylor Diagrams per Variable
======================================================
Computes (on obs grid): normalised std deviation and Pearson correlation
between regridded model and obs for annual and per-season subsets.

One Taylor diagram per variable with seasonal + annual points.

Output → postproc/results/taylor/
  taylor_<var>_<year>.png

Usage:
    python3 src/06_taylor_diagram.py [--year 2000] [--vars pr,tasmax,tasmin]
"""

import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_parser import *

import netCDF4 as nc
from netCDF4 import num2date
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import warnings; warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, default=YEAR_START)
parser.add_argument("--vars", default=",".join(VARIABLES))
args    = parser.parse_args()
YEAR    = args.year
varlist = [v.strip() for v in args.vars.split(",")]
TAYLOR_DIR.mkdir(parents=True, exist_ok=True)

print(f"\n{'═'*60}")
print(f"  06_taylor_diagram — year {YEAR}")
print(f"{'═'*60}")

# ─── Colour scheme per season ────────────────────────────────────────────────
SEASON_STYLE = {
    "Annual": {"color": "#2D3142", "marker": "D", "size": 90},
    "DJF":    {"color": "#4ECDC4", "marker": "o", "size": 70},
    "MAM":    {"color": "#6CBF6C", "marker": "s", "size": 70},
    "JJA":    {"color": "#E8505B", "marker": "^", "size": 70},
    "SON":    {"color": "#F4A259", "marker": "P", "size": 70},
}


def load_nc(fpath, var):
    with nc.Dataset(fpath) as ds:
        data    = ds.variables[var][:]
        t       = ds.variables["time"][:]
        t_units = ds.variables["time"].units
    return data, t, t_units


def month_mask(t, tunits, months):
    dates = num2date(t, tunits, calendar="standard")
    return np.array([d.month in months for d in dates])


def taylor_stats(obs_flat, mod_flat):
    """Returns (normalised_std, correlation, RMSE_normalised)."""
    # Remove NaN pairs
    valid = np.isfinite(obs_flat) & np.isfinite(mod_flat)
    o = obs_flat[valid]; m = mod_flat[valid]
    if len(o) < 5:
        return np.nan, np.nan, np.nan
    std_o = np.std(o, ddof=1); std_m = np.std(m, ddof=1)
    if std_o == 0:
        return np.nan, np.nan, np.nan
    r = np.corrcoef(o, m)[0, 1]
    nstd = std_m / std_o
    # RMSE normalised
    rmse_n = np.sqrt(nstd**2 + 1 - 2 * nstd * r)
    return nstd, r, rmse_n


def taylor_diagram(ax, stats_dict):
    """
    Draw Taylor diagram on ax.
    stats_dict: {'label': (nstd, corr, rmse_n)}
    """
    # Draw reference circle at r=1 (perfect model)
    theta = np.linspace(0, np.pi/2, 200)

    # Correlation arcs
    for r_val in [0.5, 0.7, 0.9, 0.95, 0.99]:
        angle = np.arccos(r_val)
        ax.plot([0, 2.5*np.cos(angle)], [0, 2.5*np.sin(angle)],
                color="gray", lw=0.5, linestyle=":", alpha=0.7)
        ax.annotate(f"r={r_val}", xy=(2.5*np.cos(angle), 2.5*np.sin(angle)),
                    fontsize=7, color="gray", ha="center")

    # STD arcs
    for std_val in [0.5, 1.0, 1.5, 2.0]:
        arc_theta = np.linspace(0, np.pi/2, 200)
        ax.plot(std_val*np.cos(arc_theta), std_val*np.sin(arc_theta),
                color="gray", lw=0.4, linestyle="--", alpha=0.5)

    # RMSE circles centred on reference (1, 0)
    for rmse_val in [0.5, 1.0, 1.5]:
        circ_theta = np.linspace(0, 2*np.pi, 300)
        cx = 1 + rmse_val * np.cos(circ_theta)
        cy = rmse_val * np.sin(circ_theta)
        # Only draw in first quadrant
        mask = (cx >= 0) & (cy >= 0)
        ax.plot(cx[mask], cy[mask], color="#AAAAAA", lw=0.6,
                linestyle="-.", alpha=0.6)
        if rmse_val <= 1.5:
            ax.annotate(f"RMSE={rmse_val}", xy=(1+rmse_val, 0),
                        fontsize=7, color="#888888")

    # Reference point (obs)
    ax.scatter([1], [0], s=120, c="black", marker="*", zorder=10, label="Obs (ref.)")

    # Model points
    handles = [ax.scatter([], [], s=100, c="black", marker="*", label="Obs (ref.)")]
    for label, (nstd, r, rmse_n) in stats_dict.items():
        if np.isnan(nstd) or np.isnan(r):
            continue
        style = SEASON_STYLE.get(label, {"color": "purple", "marker": "o", "size": 70})
        angle = np.arccos(np.clip(r, -1, 1))
        x = nstd * np.cos(angle)
        y = nstd * np.sin(angle)
        sc = ax.scatter(x, y, s=style["size"], c=style["color"],
                        marker=style["marker"], zorder=8, edgecolors="k", lw=0.5)
        handles.append(plt.Line2D([0],[0], marker=style["marker"],
                                  color="w", markerfacecolor=style["color"],
                                  markeredgecolor="k", markersize=8, label=label))

    ax.set_xlim(0, 2.5); ax.set_ylim(0, 2.5)
    ax.set_xlabel("Normalised Standard Deviation", fontsize=10)
    ax.set_ylabel("Normalised Standard Deviation", fontsize=10)
    ax.spines[["right","top"]].set_visible(False)

    # Correlation axis label
    ax.annotate("Pearson Correlation", xy=(1.25, 0.05), fontsize=9,
                ha="center", color="gray", rotation=-45)

    return handles


def process_var(var, year):
    mod_f = DATA_DIR / f"model_{var}_on_obs_{year}.nc"
    obs_f = DATA_DIR / f"obs_{var}_{year}.nc"

    if not mod_f.exists() or not obs_f.exists():
        print(f"  ⚠  {var}: files missing, run 01+02 first")
        return

    mod_data, mt, mtu = load_nc(mod_f, var)
    obs_data, ot, otu = load_nc(obs_f, var)

    # Align time
    n = min(mod_data.shape[0], obs_data.shape[0])
    mod_data = mod_data[:n]; obs_data = obs_data[:n]; mt = mt[:n]

    stats = {}

    # Annual
    o_flat = obs_data.ravel()
    m_flat = mod_data.ravel()
    stats["Annual"] = taylor_stats(o_flat, m_flat)

    # Seasonal
    for sname, months in SEASONS.items():
        mask = month_mask(mt, mtu, months)
        if mask.sum() == 0:
            continue
        o_s = obs_data[mask].ravel()
        m_s = mod_data[mask].ravel()
        stats[sname] = taylor_stats(o_s, m_s)

    # Print table
    cfg = MODEL[var]
    print(f"\n  {var}  Taylor statistics:")
    print(f"  {'Period':>8}  {'Norm.STD':>9}  {'r':>7}  {'RMSE_n':>8}")
    for label, (ns, r, rn) in stats.items():
        ns_s = f"{ns:.3f}" if np.isfinite(ns) else " n/a "
        r_s  = f"{r:.3f}"  if np.isfinite(r)  else " n/a "
        rn_s = f"{rn:.3f}" if np.isfinite(rn) else " n/a "
        print(f"  {label:>8}  {ns_s:>9}  {r_s:>7}  {rn_s:>8}")

    # Plot
    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor("#FAFAFA")
    handles = taylor_diagram(ax, stats)
    ax.legend(handles=handles, loc="upper right", fontsize=9,
              framealpha=0.8, title="Period")
    ax.set_title(
        f"Taylor Diagram  —  {cfg['long_name']}  —  {year}\n"
        f"RegCM r3km vs {OBS[var]['label']}  |  Morocco domain",
        fontsize=11, fontweight="bold"
    )
    out = TAYLOR_DIR / f"taylor_{var}_{year}.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✔ {out.name}")


for var in varlist:
    print(f"\n  ── {var} ──────────────────────")
    process_var(var, YEAR)

print(f"\n{'═'*60}")
print(f"  ✔  Taylor diagrams done — {TAYLOR_DIR}")
print(f"{'═'*60}\n")
