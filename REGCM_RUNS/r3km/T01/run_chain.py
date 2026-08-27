#!/usr/bin/env python3
# ==============================================================================
# Script Name: run_chain.py
# Description: Automatic chaining script for sequential job submission
# Author: M. El Aabaribaoune (@um6p)
# Note: This is an HPC-specific extension developed for managing RegCM simulations
# ==============================================================================

import sys
import os
import subprocess
from datetime import datetime, timedelta

# ==========================================
# CHAINING CONFIGURATION
# ==========================================
MDATE0 = "1999010100"       # Global start date (and date of the 1st run)
MDATE_FINAL = "2005010100"  # Run until end of 2004
PERIOD_LENGTH = "15D"        # "1M" (1 month), "1D" (1 day), "15D" (15 days), etc.

TEMPLATE = "templates/test_0010.template.in"
OUTPUT_IN = "test_0010.in"
JOB_SCRIPT = "job.sh"
STATE_FILE = "chain_state.txt"
# ==========================================

def add_period(dt_str, period):
    dt = datetime.strptime(dt_str, "%Y%m%d%H")
    if period == '1M':
        month = dt.month
        year = dt.year
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        return dt.replace(year=year, month=month).strftime("%Y%m%d%H")
    elif period == '1D':
        return (dt + timedelta(days=1)).strftime("%Y%m%d%H")
    elif period == '15D':
        return (dt + timedelta(days=15)).strftime("%Y%m%d%H")
    else:
        raise ValueError(f"Unsupported period {period}.")

def main():
    if not os.path.exists(STATE_FILE):
        print(f"Initialization: Creating the first {OUTPUT_IN} file starting from {MDATE0}")
        mdate1 = MDATE0
        ifrest = ".false."
    else:
        with open(STATE_FILE, "r") as f:
            mdate1 = f.read().strip()
        ifrest = ".true."

    if mdate1 >= MDATE_FINAL:
        print(f"SUCCESS: Simulation finished! The final date {MDATE_FINAL} has been reached.")
        return

    mdate2 = add_period(mdate1, PERIOD_LENGTH)

    if mdate2 > MDATE_FINAL:
        mdate2 = MDATE_FINAL

    print(f"-> Configuration for the period: {mdate1} to {mdate2}")

    with open(TEMPLATE, "r") as f:
        content = f.read()

    content = content.replace("__MDATE0__", MDATE0)
    content = content.replace("__MDATE_FINAL__", MDATE_FINAL)
    content = content.replace("__MDATE1__", mdate1)
    content = content.replace("__MDATE2__", mdate2)
    content = content.replace("__IFREST__", ifrest)

    with open(OUTPUT_IN, "w") as f:
        f.write(content)

    # Save the state for the NEXT run
    with open(STATE_FILE, "w") as f:
        f.write(mdate2)

    # If running in init mode, do not submit
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        print(f"--init mode finished. {OUTPUT_IN} file generated.")
        print(f"Please run 'sbatch {JOB_SCRIPT}' to start the chaining process.")
    else:
        print(f"Automatically submitting {JOB_SCRIPT}...")
        subprocess.run(["sbatch", JOB_SCRIPT])

if __name__ == "__main__":
    main()
