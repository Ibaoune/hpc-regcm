# RESOURCE AVAILABILITY REPORT (CPU & STORAGE)

**Author**: M. El Aabaribaoune (@um6p)

## 1. COMPUTE RESOURCES (CPU - SLURM)

- **Account:** CLIMAT-UM6P-ST-IWRI-7KSIFKVWKUY-DEFAULT-CPU
- **Available allocated hours:** 1,000,000 hours (Completely full/Intact).
- **CPU Conclusion:** We have a colossal compute budget. Compute time is absolutely not a problem to continue this 11-year simulation.

## 2. STORAGE SPACE (LUSTRE : /srv/lustre01)

- **Total mount point capacity (Project Quota):** ~319 TB
- **Currently used space:** ~272 TB (of which 266.5 TB is used by our project `mohammad.elaabaribao` !)
- **AVAILABLE FREE SPACE:** ~47 TB

## 3. HOW MUCH LONGER CAN WE SIMULATE?

- **Cost of current simulation (without changing anything):** ~1.25 TB per simulated month.
- **Total requirement for 11 years:** ~162 TB (without compression).
- **Remaining capacity:** ~47 TB free.
- **RESULT:** The recent storage upgrade has given us some breathing room (we gained about 45 TB!). We can now safely simulate about **37 months (just over 3 years)** without changing our output frequency. However, we still cannot complete the full 11-year simulation (162 TB required) on this current capacity without optimizing the outputs.

> [!CAUTION]
> **RECOMMENDATION (URGENT OPTIMIZATION)**
> To avoid running out of space in the middle of our 11-year run, we **must** reduce the ATM frequency (`atmfrq`) to 12 or 24 hours. Doing so will cut the annual storage from 14.7 TB to 8.2 TB or 5.4 TB, which might allow us to fit the remaining 9 years into the 47 TB available.
