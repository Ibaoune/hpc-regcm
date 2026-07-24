# SCENARIOS AND STORAGE STRATEGY (2001 - 2004)

This document explains what was done during the 1999-2000 period, how it impacts storage, and proposes concrete scenarios to successfully run the next 4 years (2001 to 2004 inclusive) within the remaining 47 TB quota.

## 1. WHAT WE DID FOR 1999 - 2000
During the first two years of the simulation, we used a very high-frequency output configuration (defined in `test_0010.in`):

- **ATM (3D Atmosphere):** 6-hourly (4 outputs per day)
- **RAD (Radiation):** 6-hourly (4 outputs per day)
- **SRF (Surface):** 1-hourly (24 outputs per day)
- **SHF (Sensible Heat Flux):** 1-hourly (24 outputs per day)
- **STS (Statistics):** Daily (1 output per day)

**The Cost:** This configuration generates massive files (e.g., 25 GB per daily ATM file). In total, it consumes **~14.7 TB per simulated year**. 
For the ~2 years already completed (1999 and 2000), we have generated nearly 30 TB of data.

---

## 2. THE CHALLENGE FOR 2001 - 2004
You want to simulate 4 additional years (2001, 2002, 2003, 2004).

- **Current Free Space:** ~47 TB
- **Space required with current config (14.7 TB/year * 4 years):** ~58.8 TB

**Conclusion:** If we do not change anything, the simulation will crash before reaching the end of 2004 because 58.8 TB > 47 TB. We **must** optimize.

---

## 3. OPTIMIZATION SCENARIOS FOR 2001 - 2004

Here is exactly what we gain by changing specific frequencies.

### Scenario A: Reduce ATM to 12-hourly (`atmfrq = 12.`)
- **Why?** ATM is the heaviest file (64% of total storage). By going from 6h to 12h, we cut its size in half.
- **Gain:** We save **4.7 TB per year**.
- **New Cost:** 10.0 TB per year.
- **Cost for 4 years (2001-2004):** 40 TB.
- **Result:** **SUCCESS.** It fits inside the 47 TB limit, leaving 7 TB of headroom for logs and temporary files.

### Scenario B: Reduce ATM to 12-hourly AND RAD to 12-hourly (`atmfrq = 12.`, `radfrq = 12.`)
- **Why?** RAD is the second heaviest file (25% of storage). 
- **Gain:** We save 4.7 TB (from ATM) + 1.85 TB (from RAD) = **6.55 TB per year**.
- **New Cost:** 8.15 TB per year.
- **Cost for 4 years (2001-2004):** 32.6 TB.
- **Result:** **EXCELLENT.** This gives us a very safe margin (14.4 TB free) and makes post-processing much faster.

### What about STS, SRF, or SHF?
- **STS (Daily):** Consumes only 25 GB/year (0.025 TB). Changing this gives **no visible gain**.
- **SHF (Hourly):** Consumes only 135 GB/year (0.13 TB). Changing this gives **no visible gain**.
- **SRF (Hourly):** Consumes 1 TB/year. We could change it to 3-hourly to save ~0.6 TB/year, but hourly surface data is usually very important for analysis (precipitation peaks, max/min temps). **Recommendation: Keep SRF at 1-hourly.**

---

## 4. HOW TO PROCEED NOW (ACTION PLAN)

To safely launch the period 2001-2004, here is the exact procedure we recommend:

1. **Modify the template:**
   Open `templates/test_0010.template.in` and locate the `&outparam` section.
2. **Apply Scenario B (Safest approach):**
   Change:
   ```fortran
   atmfrq = 6.
   radfrq = 6.
   ```
   To:
   ```fortran
   atmfrq = 12.
   radfrq = 12.
   ```
3. **Leave everything else as it is:** Keep `srffrq = 1.` and `ifsts = .true.` to retain high-resolution surface data.
4. **Restart the Job Chaining:**
   You can now safely restart your simulation for 2001. The output files will be significantly lighter, the model will run slightly faster (less I/O time writing to Lustre), and we are guaranteed not to crash the server due to space limits before 2005.
