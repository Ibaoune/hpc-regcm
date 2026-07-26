# T01 / archive_periods

**Overview**:
This directory acts as a structured archiving system for data. To prevent the `output/` directory from overflowing Lustre quotas during long continuous runs, the `run_chain.py` script (or post-processing scripts) moves completed simulation periods (e.g., 199901, 199902) into subdirectories here.

**Structure**:
Subdirectories are typically named by the date ranges (e.g., `199901`, `1999121500-2000011500_ok`). Suffixes like `_ok` or `_bug` signify the success or failure of that particular time slice.
