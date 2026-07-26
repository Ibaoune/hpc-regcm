# SRC_REGCM / scripts / build_regcm

**Author**: M. El Aabaribaoune (@um6p)

**Overview**:
A collection of bash scripts strictly dedicated to the configuration, compilation, and environment setup of the RegCM source code.

**Files**:
- **`compile_regcm.sh`**: Executes the `./configure` and `make` pipeline to build the model binaries.
- **`regcm_clean.sh`**: Runs `make clean` or `make distclean` to wipe out old `.o` and `.mod` compiled object files, resetting the source tree for a fresh compilation.
- **`set_regcm_env_varibales.sh`**: Exports critical environment variables (like `$DIR_WORKSPACE`, `$DIR_REGCM`) so that build scripts and run scripts know exactly where the project paths are located.
- **`create_inputs.sh`**: A utility script to generate or structure necessary input directories or placeholder files required before compilation or initialization.
