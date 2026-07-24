#!/usr/bin/env python3
# ==============================================================================
# Script Name: generate_forcing_report.py
# Description: Generates report for forcing data and initial conditions
# Author: M. El Aabaribaoune (@um6p)
# Note: This is an HPC-specific extension developed for managing RegCM simulations
# ==============================================================================
import os
import subprocess
import glob
import re

report_file = "doc/report_forcing_IC.txt"
ic_dir = "../T00_IC/input"
prefix = "module purge && module load GCC/11.2.0 OpenMPI/4.1.1-GCC-11.2.0 netCDF/4.8.1-gompi-2021b && "

def get_ncdump_h(filepath):
    cmd = prefix + f"ncdump -h {filepath}"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout

def parse_global_attributes(ncdump_output):
    attrs = {}
    in_global = False
    for line in ncdump_output.split('\n'):
        if line.strip() == "// global attributes:":
            in_global = True
            continue
        if in_global:
            m = re.match(r'\s*:([a-zA-Z0-9_]+)\s*=\s*(.*)\s*;', line)
            if m:
                attrs[m.group(1)] = m.group(2).strip('"')
    return attrs

def parse_variables(ncdump_output):
    vars_list = []
    in_vars = False
    for line in ncdump_output.split('\n'):
        if line.strip() == "variables:":
            in_vars = True
            continue
        if line.strip() == "// global attributes:":
            break
        if in_vars:
            m = re.match(r'\s*\w+\s+([a-zA-Z0-9_]+)\(.*\)\s*;', line)
            if m:
                vars_list.append(m.group(1))
    return vars_list

def main():
    icbc_files = sorted(glob.glob(f"{ic_dir}/*_ICBC.*.nc"))
    sst_files = sorted(glob.glob(f"{ic_dir}/*_SST.nc"))
    
    with open(report_file, "w") as f:
        f.write("============================================================\n")
        f.write(" DOCUMENTATION DES FORÇAGES ET CONDITIONS INITIALES (IC/BC)\n")
        f.write("============================================================\n\n")
        
        f.write("1. CONDITIONS AUX LIMITES ET INITIALES (ICBC)\n")
        f.write("---------------------------------------------\n")
        if not icbc_files:
            f.write("Aucun fichier ICBC trouvé.\n")
        else:
            first_icbc = icbc_files[0]
            f.write(f"Fichier analysé : {os.path.basename(first_icbc)}\n")
            f.write(f"Nombre total de fichiers ICBC trouvés : {len(icbc_files)}\n")
            
            ncdump_out = get_ncdump_h(first_icbc)
            attrs = parse_global_attributes(ncdump_out)
            
            f.write("\nMétadonnées globales :\n")
            for k, v in attrs.items():
                f.write(f"  - {k}: {v}\n")
                
            vars_list = parse_variables(ncdump_out)
            f.write("\nVariables incluses dans le forçage :\n")
            f.write(f"  {', '.join([v for v in vars_list if v not in ['lon', 'lat', 'time', 'x', 'y', 'kz', 'crs']])}\n")
            
            f.write(f"\nPoids moyen par fichier mensuel : ~95 Go (d'après l'inventaire)\n")
            
        f.write("\n============================================================\n")
        f.write("2. FORÇAGE OCÉANIQUE (SST)\n")
        f.write("---------------------------------------------\n")
        if not sst_files:
            f.write("Aucun fichier SST trouvé.\n")
        else:
            sst_file = sst_files[0]
            f.write(f"Fichier analysé : {os.path.basename(sst_file)}\n")
            
            ncdump_out = get_ncdump_h(sst_file)
            attrs = parse_global_attributes(ncdump_out)
            
            f.write("\nMétadonnées globales :\n")
            for k, v in attrs.items():
                f.write(f"  - {k}: {v}\n")
                
            vars_list = parse_variables(ncdump_out)
            f.write("\nVariables incluses :\n")
            f.write(f"  {', '.join([v for v in vars_list if v not in ['lon', 'lat', 'time', 'x', 'y', 'crs']])}\n")
            
        f.write("\n============================================================\n")
        f.write("3. SURFACE TERRESTRE (LANDUSE / TEXTURE)\n")
        f.write("---------------------------------------------\n")
        f.write("Fichiers binaires/texte utilisés :\n")
        f.write("  - test_001_LANDUSE\n")
        f.write("  - test_001_TEXTURE\n")
        
        f.write("\n============================================================\n")
        f.write(" RÉSUMÉ DE LA CONFIGURATION (d'après test_0010.in)\n")
        f.write("============================================================\n")
        f.write("  - ssttyp = 'ERA5'\n")
        f.write("  - dattyp = 'ERA5'\n")
        f.write("  - Date de début globale (gdate1) : 1999-01-01\n")
        f.write("  - Date de fin globale (gdate2) : Varie selon la période\n")
        f.write("  - Fréquence des conditions aux limites (ibdyfrq) : 6 heures\n")

    print(f"Rapport généré avec succès dans {report_file}")

if __name__ == "__main__":
    main()
