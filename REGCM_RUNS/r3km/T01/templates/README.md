# T01 / templates

**Author**: M. El Aabaribaoune (@um6p)

**Overview**:
This directory stores template files that are read and dynamically modified by Python automation scripts.

**Files**:
- **`test_0010.template.in`**: A templated version of the RegCM namelist. `run_chain.py` reads this file, replaces placeholder variables (like `$START_DATE`, `$END_DATE`) with actual dates, and writes the resulting `test_0010.in` for the next simulation period.
