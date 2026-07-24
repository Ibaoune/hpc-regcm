# RESOURCE AVAILABILITY REPORT (CPU & STORAGE)

## 1. COMPUTE RESOURCES (CPU - SLURM)

- **Account:** CLIMAT-UM6P-ST-IWRI-7KSIFKVWKUY-DEFAULT-CPU
- **Available allocated hours:** 1,000,000 hours (Completely full/Intact).
- **CPU Conclusion:** You have a colossal compute budget. Compute time is absolutely not a problem to continue this 11-year simulation.

## 2. STORAGE SPACE (LUSTRE : /srv/lustre01)

- **Total mount point capacity:** 273 TB
- **Currently used space:** 271 TB (of which 266.5 TB is used by you `mohammad.elaabaribao` !)
- **AVAILABLE FREE SPACE:** 2.2 TB

## 3. HOW MUCH LONGER CAN YOU SIMULATE?

- **Cost of current simulation (without changing anything):** ~1.25 TB per simulated month.
- **Remaining capacity:** 2.2 TB free.
- **RESULT:** You can barely simulate **1.5 months (about 45 to 50 simulation days)** before COMPLETELY saturating the `/srv/lustre01` file system.

> [!CAUTION]
> **CRITICAL RECOMMENDATION (URGENT)**
> **WARNING:** Disk space is almost saturated (99% usage). If you restart the Job Chaining now with the same frequencies (notably ATM at 6 hours which takes 773 GB/month), the model will crash abruptly in less than 2 simulated months with a "No space left on device" error.

**IMMEDIATE ACTIONS:**
1. **Purge:** Delete old useless files from your space (you occupy 266 TB alone!). Look particularly at very heavy ICBC forcing files if they are no longer used, or old tests.
2. **Optimize the simulation:** Absolutely change the ATM frequency (`atmfrq`) to 12 or 24 hours in `templates/test_0010.template.in` to drastically reduce file creation.
