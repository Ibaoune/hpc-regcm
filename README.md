# Projet RegCM - Modélisation Climatique Régionale (Maroc)

Ce dépôt contient l'environnement d'exécution, la configuration et les scripts pour les simulations climatiques régionales sur le Maroc à l'aide du modèle **RegCM** (v4.5).

## 🌍 Région Simulée
La simulation cible le Maroc et ses environs avec une haute résolution spatiale.
- **Résolution** : 3.0 km (`ds = 3.0`)
- **Grille** : 920 x 1084 (`iy = 920`, `jx = 1084`), 50 niveaux verticaux (`kz = 50`)
- **Centre du domaine** : Latitude 32.50° N (`clat`), Longitude -12.50° E (`clon`)
- **Projection** : Rotated Lat/Lon (`ROTLLR`)

## 📂 Organisation du Projet

Le projet est structuré pour gérer de grands volumes de données en environnement HPC (Lustre) :

- `README.md` : Ce fichier de documentation.
- `.gitignore` : Ignore tous les fichiers lourds (NetCDF, logs, données).
- `REGCM_RUNS/` : Dossier principal contenant les expériences.
  - `r3km/` : Simulations à 3 km de résolution.
    - `T01/` : Run de production principal. Contient le `job.sh` et la configuration.
    - `T00_IC/` : Conditions initiales.
- `REGCM_GLOBEDAT/` : Données globales d'entrée (non versionné).
- `SRC_REGCM/` : Code source de RegCM, spécifiquement `RegCM-CLM45` (non versionné ici).
- `simus_from_Graziano/` : Simulations de référence (non versionné).

## ⚙️ Configuration Principale (`test_0010.in`)
Le fichier `REGCM_RUNS/r3km/T01/test_0010.in` contrôle le comportement du modèle.
### Fréquences d'écriture :
- **ATM (Champs 3D)** : Toutes les 6 heures (`atmfrq = 6.0`)
- **RAD (Radiations)** : Toutes les 6 heures (`radfrq = 6.0`)
- **SRF (Surface)** : Toutes les 1 heures (`srffrq = 1.0`) - *Attention, très gourmand en espace*
- **SHF (Flux surface)** : Toutes les 1 heures (suit `srffrq`)
- **STS (Statistiques)** : Moyennes/Extrêmes journaliers (1 fichier/jour)

*Note : La variable `outnwf = 1.0` indique que le modèle génère **1 fichier par jour** pour ces variables.*

## 🚀 Exécution d'une Simulation
Le projet utilise le gestionnaire de tâches SLURM sur le cluster Toubkal.

1. **Préparation** : Vérifiez que vos modules sont corrects (GCC, OpenMPI, netCDF, HDF5).
2. **Soumission** :
   ```bash
   cd REGCM_RUNS/r3km/T01
   sbatch job.sh
   ```
3. **Ressources allouées** : 28 nœuds x 32 tâches (896 cœurs MPI).
4. **Logs** : Les logs SLURM se trouvent dans `REGCM_RUNS/r3km/T01/logs/`.

## 🧹 Bonnes Pratiques
- **Espace disque** : Les sorties génèrent environ **1.4 To par mois simulé**. Surveillez votre quota Lustre.
- **Git** : N'ajoutez **jamais** de fichiers `.nc` (NetCDF) ou `.tmp` au dépôt Git. Le `.gitignore` est configuré pour les bloquer.
- **Nettoyage** : Purgez régulièrement les anciens fichiers de logs et les fichiers temporaires.
