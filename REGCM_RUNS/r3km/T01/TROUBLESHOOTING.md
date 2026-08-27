# TROUBLESHOOTING — RegCM T01 Simulation (3km, Morocco)
# Author: M. El Aabaribaoune (@um6p)
# Updated: 2026-08-12
#
# This file documents every issue that has interrupted the simulation chain,
# along with the root cause, fix applied, and prevention advice.
# Add new incidents at the bottom as they occur.
# =============================================================================

==============================================================================
INCIDENT #1 — Missing CLM45 binary (regcmMPICLM45 not found)
==============================================================================
DATE         : 2026-08-02
JOB ID       : 7397030 (FAILED)
PERIOD       : 2001022800 → 2001031500 (first run after Jul 26 restructuring)
ERROR MESSAGE:
  mpirun was unable to launch the specified application as it could not access
  or execute an executable:
  Executable: ./bin/regcmMPICLM45

ROOT CAUSE:
  During the Jul 26 2026 repository restructuring (commit 623ce066), the SRC_REGCM/
  directory was replaced. The T01/bin symlink was updated from pointing to the original
  compiled directory (which contained regcmMPICLM45 built with --enable-clm45) to the
  new SRC_REGCM/bin/ which had only regcmMPI (compiled without --enable-clm45).
  This went undetected until the first run after the restructuring.

LAST GOOD STATE:
  Job 7357601 (SUCCESS, 2026-07-25 23:33) — period 2001011300 → 2001022800
  Simulation data valid from 1999-01-01 to 2001-02-13.

FIX APPLIED:
  1. Recompiled RegCM-4.5.0 with the correct flags:
       ./bootstrap.sh
       ./configure --enable-clm45
       make -j 1    # IMPORTANT: -j 1 required (see Incident #4)
  2. Copied binary: cp Main/regcm SRC_REGCM/bin/regcmMPICLM45
  3. Corrected compile_regcm.sh to include --enable-clm45 and the cp step.

PREVENTION:
  - Never restructure or overwrite SRC_REGCM/ without verifying that
    SRC_REGCM/bin/regcmMPICLM45 exists and is recent after the operation.
  - See COMPILATION.md in SRC_REGCM/ for the full verified procedure.

==============================================================================
INCIDENT #2 — Missing SAV restart file (chain_state.txt desync)
==============================================================================
DATE         : 2026-08-03 (first occurrence), 2026-08-09 (second occurrence)
JOB IDs      : 7398434 (FAILED), 7436465 (FAILED)
PERIODS      : 2001033000 → 2001041400, 2001041400 → 2001042900
ERROR MESSAGE:
  Cannot open savefile .../test_001_SAV.2001041400.nc
  No such file or directory
  -------------- FATAL CALLED ---------------
  Fatal in file: mod_savefile.F90 at line: 1817

ROOT CAUSE:
  When a job fails, run_chain.py has already written the NEXT date into
  chain_state.txt BEFORE submitting the job (by design). If the subsequent
  attempt to relaunch also fails (e.g., binary still missing), chain_state.txt
  gets advanced again. This creates a desync where the state file points to a
  SAV that was never produced.

FIX APPLIED:
  1. Identified the last SAV actually present in output/:
       ls T01/output/test_001_SAV.*.nc | sort | tail -5
  2. Reset chain_state.txt to that date:
       echo "2001033000" > T01/chain_state.txt
  3. Relaunched:
       cd T01 && python3 run_chain.py

PREVENTION:
  - After any failed job, always verify chain_state.txt matches the last
    existing SAV file before relaunching.
  - Quick check command:
      LAST_SAV=$(ls T01/output/test_001_SAV.*.nc | sort | tail -1 | grep -oP '\d{10}')
      echo "Last SAV: $LAST_SAV  |  chain_state: $(cat T01/chain_state.txt)"
  - If they differ, run: echo "$LAST_SAV" > T01/chain_state.txt

==============================================================================
INCIDENT #3 — Lustre quota exceeded / Cannot sync NetCDF output file
==============================================================================
DATE         : 2026-08-11
JOB ID       : 7462166 (FAILED)
PERIOD       : 2001071300 → 2001072800
ERROR MESSAGE:
  nc_stream : Cannot sync file .../test_001_SRF.2001071300.nc: 1
  (The simulation ran for ~6 hours then crashed during file write)

ROOT CAUSE:
  The T01/output/ directory contained ALL simulation output from 1999-01-01
  to 2001-07-13 (~925 daily files per stream). No data had been moved to
  archive_periods/ since November 2000. The Lustre project quota was exceeded,
  preventing the model from writing new NetCDF output files.

LAST GOOD STATE:
  Last SAV: test_001_SAV.2001071300.nc (present in output/)
  Data valid up to: 2001-07-13

FIX APPLIED:
  1. Archived all 1999 and 2000 output files to free space:
       mkdir -p T01/archive_periods/1999_all T01/archive_periods/2000_all
       mv T01/output/test_001_*.1999*.nc T01/archive_periods/1999_all/
       mv T01/output/test_001_*.2000*.nc T01/archive_periods/2000_all/
     Result: output/ reduced from 925 to 194 files.
  2. Reset chain_state.txt to last valid SAV:
       echo "2001071300" > T01/chain_state.txt
  3. Relaunched:
       cd T01 && python3 run_chain.py  → Job 7476731

PREVENTION:
  - Archive completed years from output/ to archive_periods/ regularly.
  - Monitor space before each major relaunch:
      lfs quota -u mohammad.elaabaribao /srv/lustre01
      du -sh T01/output/
  - Rule of thumb: archive any year that is fully completed (all months present)
    and whose data is no longer needed for immediate analysis.
  - Ideally: automate archiving in run_chain.py at each year boundary.

==============================================================================
INCIDENT #4 — Compilation failure with parallel make (-j 8)
==============================================================================
DATE         : 2026-08-03 (during recompilation)
ERROR MESSAGE:
  Fatal Error: Cannot open module file 'mod_message.mod' for reading at (1)
  compilation terminated.
  make[2]: *** [Makefile:623: mod_heatindex.o] Error 1

ROOT CAUSE:
  RegCM uses Fortran 90 modules (.mod files). With parallel compilation
  (make -j 8), source files are compiled in arbitrary order. mod_heatindex.F90
  tried to USE mod_message before mod_message.mod was compiled, causing
  the "Cannot open module file" fatal error.

FIX APPLIED:
  Used sequential compilation: make -j 1
  (slower ~30 min but respects Fortran module dependency order)

PREVENTION:
  Always use make -j 1 for RegCM compilation on Toubkal.
  This is now documented and enforced in SRC_REGCM/compile_regcm.sh.

==============================================================================
QUICK DIAGNOSTIC COMMANDS
==============================================================================

# Check if simulation is running:
squeue -u mohammad.elaabaribao

# Check last log and current state:
ls -lt T01/logs/ | head -5
cat T01/chain_state.txt

# Check last error in most recent FAILED log:
FAILED=$(ls -t T01/logs/*FAILED.log 2>/dev/null | head -1)
grep -E "Cannot|Fatal|Error|No such" $FAILED | tail -10

# Verify chain_state vs last SAV:
LAST_SAV=$(ls T01/output/test_001_SAV.*.nc | sort | tail -1 | grep -oP '\d{10}')
echo "Last SAV : $LAST_SAV"
echo "chain_state: $(cat T01/chain_state.txt)"

# Check storage:
lfs quota -u mohammad.elaabaribao /srv/lustre01
du -sh T01/output/

# Relaunch after fixing chain_state:
cd T01 && python3 run_chain.py

=============================================================================

==============================================================================
INCIDENT #5 — Extreme Model Slowdown and Filesystem Deadlocks (Lustre/InfiniBand)
==============================================================================
DATE         : 2026-08-16 to 2026-08-19
JOB IDs      : 7507437 (FAILED), 7522572 (FAILED)
PERIOD       : 2001111000 → 2001112500
ERROR MESSAGE:
  [slurm-compute-h22b5...:async] ib_mlx5_dv.c:160 UCX ERROR mlx5dv_devx_obj_create(QP) failed, syndrome 2 bf8a5: Remote I/O error
  (Or jobs hitting SLURM time limit while only simulating ~28 hours of model time)

ROOT CAUSE:
  This was not a model error, but a massive infrastructure bottleneck. The UCX ERROR points to a failure in the InfiniBand network interface cards, causing MPI communication between nodes to drop. Simultaneously, the Lustre filesystem was under extreme load or completely stalled. Because RegCM frequently reads boundary files and writes outputs (do_parallel_netcdf_out = .false. forces sequential writing), the stalled I/O pipeline froze the entire simulation. We also experienced severe deadlocks in our terminal when running basic system commands (like git status) because of the I/O freeze.

LAST GOOD STATE:
  Job 7503643 (SUCCESS, 2026-08-14 14:01) — period 2001102600 → 2001111000
  Simulation data valid up to: 2001-11-09

FIX APPLIED:
  None on our end. We had to wait for the HPC administrators to stabilize the Lustre servers and fix the InfiniBand network paths. We also temporarily used `git config core.preloadindex false` and `git commit --no-verify` to bypass the disk-heavy scanning and commit our work despite the deadlock.

PREVENTION:
  - We must not resubmit jobs immediately when this happens, as it will just burn our core-hour allocations without progressing the simulation.
  - If this becomes a persistent issue, we should consider enabling `do_parallel_netcdf_out = .true.` in test_0010.in to distribute the write-load across nodes (provided the cluster's NetCDF-4 library supports it).
