# RegCM Compilation Guide (Toubkal HPC)

**Author**: M. El Aabaribaoune (@um6p)

This document explains how to compile the adapted RegCM v4.5 model on the Toubkal cluster
to produce the `regcmMPICLM45` executable required to run the T01 simulation.

---

## Important Notes

> **Why `-j 1`?** RegCM uses Fortran 90 modules. With parallel `make -j N`, source files can
> be compiled before their `.mod` dependencies are ready, causing:
> ```
> Fatal Error: Cannot open module file 'mod_message.mod' for reading
> ```
> Always use **`make -j 1`** (sequential). It is slower (~30 min) but reliable.

> **Why is `bin/` not in Git?** Compiled binaries are platform-specific and very large (23 MB).
> They are excluded via `.gitignore`. The source code and this guide allow the binary to be
> fully recreated at any time.

---

## Quickstart

From the `SRC_REGCM/` directory:

```bash
cd SRC_REGCM/
./compile_regcm.sh
```

This script does everything automatically (see details below).

---

## Step-by-Step Compilation

### 1. Load Environment

```bash
source arch_RegCM4.5_Tbkl.env
```

This loads the exact module versions needed on Toubkal:
- `GCC/11.2.0`
- `OpenMPI/4.1.1-GCC-11.2.0`
- `netCDF/4.8.1-gompi-2021b`
- `HDF5/1.12.1-gompi-2021b`
- `netCDF-Fortran/4.5.3-gompi-2021b`

### 2. Bootstrap (first time only, if `configure` is missing)

```bash
cd RegCM-4.5.0/
./bootstrap.sh
```

This generates the `configure` script from `configure.ac` and `Makefile.am`.

### 3. Configure with CLM45 support

```bash
./configure --enable-clm45
```

The `--enable-clm45` flag is **mandatory** to build `regcmMPICLM45` with the
Community Land Model 4.5 (CLM45) surface scheme active. Without it, only
`regcmMPI` (without CLM45) would be produced, which cannot run the `T01` simulation.

### 4. Compile (sequential)

```bash
make -j 1
```

Expected output at the end:
```
make[1]: Leaving directory '.../RegCM-4.5.0'
```

The binary is generated at `RegCM-4.5.0/Main/regcm`.

### 5. Install binary to `bin/`

```bash
cp Main/regcm ../bin/regcmMPICLM45
```

The `T01/bin` symlink points to `SRC_REGCM/bin/`, so it immediately becomes
available to the simulation job scripts.

---

## Verification

After compilation, check that the binary exists and is recent:

```bash
ls -lh SRC_REGCM/bin/regcmMPICLM45
```

Expected output:
```
-rwxrwx---+ 1 mohammad.elaabaribao ... 23M Aug  3 11:18 SRC_REGCM/bin/regcmMPICLM45
```

You can also verify CLM45 is embedded by running (it will print usage and exit):

```bash
SRC_REGCM/bin/regcmMPICLM45 --version 2>&1 | head -5
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Cannot open module file '*.mod'` | Parallel compilation race condition | Use `make -j 1` |
| `./configure: No such file or directory` | bootstrap not run | Run `./bootstrap.sh` first |
| `regcmMPICLM45: not found` | Binary not copied to `bin/` | Run `cp Main/regcm ../bin/regcmMPICLM45` |
| Module load errors | Wrong libtool version on Toubkal | Ignore `libtool` warning, it is not needed |

---

## Compilation History

| Date | CLM45 | By | Notes |
|---|---|---|---|
| Nov 2025 | ✅ | M. El Aabaribaoune | Original compile in `Model/RegCM/RegCM-Toubkal/bin/` |
| Jul 26 2026 | ❌ | restructuration | Accidentally compiled without `--enable-clm45` |
| Aug 3 2026 | ✅ | M. El Aabaribaoune | Recompiled with `--enable-clm45`, `make -j 1` |
