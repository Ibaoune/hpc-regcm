# T01 / doc / scripts

**Overview**:
Contains Python scripts designed to extract metadata, performance metrics, and variable lists from the RegCM model outputs and logs.

**Files** (Expected):
- **`generate_report.py`**: The main orchestration script that reads simulation logs and outputs, aggregates the progress, and generates a formatted Markdown report.
- **`generate_forcing_report.py`**: Specializes in verifying the integrity and timeline of the forcing data.
- **`generate_benchmark_report.py`**: Focuses on HPC performance (cores used, wall-clock time, node efficiency).
