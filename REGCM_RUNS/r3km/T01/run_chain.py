#!/usr/bin/env python3
import sys
import os
import subprocess
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION DU CHAÎNAGE
# ==========================================
MDATE0 = "1999010100"       # Date globale de début (et date du 1er run)
MDATE_FINAL = "2010010100"  # Date d'arrêt globale de la simulation
PERIOD_LENGTH = "1M"        # "1M" (1 mois), "1D" (1 jour), etc.

TEMPLATE = "templates/test_0010.template.in"
OUTPUT_IN = "test_0010.in"
JOB_SCRIPT = "job.sh"
STATE_FILE = "chain_state.txt"
# ==========================================

def add_period(dt_str, period):
    dt = datetime.strptime(dt_str, "%Y%m%d%H")
    if period == '1M':
        month = dt.month
        year = dt.year
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        return dt.replace(year=year, month=month).strftime("%Y%m%d%H")
    elif period == '1D':
        return (dt + timedelta(days=1)).strftime("%Y%m%d%H")
    else:
        raise ValueError(f"Period {period} non supportée.")

def main():
    if not os.path.exists(STATE_FILE):
        print(f"Initialisation : Création du premier fichier {OUTPUT_IN} à partir de {MDATE0}")
        mdate1 = MDATE0
        ifrest = ".false."
    else:
        with open(STATE_FILE, "r") as f:
            mdate1 = f.read().strip()
        ifrest = ".true."

    if mdate1 >= MDATE_FINAL:
        print(f"SUCCESS: Simulation terminée ! La date finale {MDATE_FINAL} a été atteinte.")
        return

    mdate2 = add_period(mdate1, PERIOD_LENGTH)

    if mdate2 > MDATE_FINAL:
        mdate2 = MDATE_FINAL

    print(f"-> Configuration pour la période : {mdate1} à {mdate2}")

    with open(TEMPLATE, "r") as f:
        content = f.read()

    content = content.replace("__MDATE0__", MDATE0)
    content = content.replace("__MDATE_FINAL__", MDATE_FINAL)
    content = content.replace("__MDATE1__", mdate1)
    content = content.replace("__MDATE2__", mdate2)
    content = content.replace("__IFREST__", ifrest)

    with open(OUTPUT_IN, "w") as f:
        f.write(content)

    # On sauvegarde l'état pour le PROCHAIN lancement
    with open(STATE_FILE, "w") as f:
        f.write(mdate2)

    # Si on est en mode initialisation, on ne soumet pas
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        print(f"Mode --init terminé. Fichier {OUTPUT_IN} généré.")
        print(f"Veuillez lancer 'sbatch {JOB_SCRIPT}' pour démarrer le chaînage.")
    else:
        print(f"Soumission automatique de {JOB_SCRIPT}...")
        subprocess.run(["sbatch", JOB_SCRIPT])

if __name__ == "__main__":
    main()
