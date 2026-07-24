---
title: "Rapport de Simulation : RegCM T01 (Maroc 3km)"
author: "mohammad.elaabaribao"
date: "21 Juillet 2026"
geometry: margin=2cm
---

# Page de garde

**Projet** : Simulation Climatique Régionale avec RegCM  
**Domaine** : Maroc et régions environnantes  
**Résolution** : 3.0 km  
**Modèle** : RegCM v4.5 (avec module CLM45)  
**Date du rapport** : 21 Juillet 2026  

---

# Résumé

Ce rapport présente une analyse complète de la simulation climatique régionale T01 réalisée sur le domaine du Maroc avec le modèle RegCM v4.5 à une résolution horizontale de 3 km. La simulation documentée s'étend de janvier 1999 à mi-novembre 2000. Le rapport détaille la configuration du modèle, les forçages initiaux et aux limites (ICBC/SST basés sur ERA5), les variables atmosphériques et de surface simulées, ainsi qu'une évaluation approfondie des ressources de calcul et de stockage nécessaires. Environ 22.5 mois de simulation ont été réalisés, générant environ 27.1 To de données sur le système de fichiers Lustre. Des recommandations critiques sont émises concernant l'optimisation des fréquences de sortie pour éviter la saturation imminente de l'espace de stockage.

---

# Introduction

La modélisation du climat régional à haute résolution est essentielle pour comprendre la dynamique atmosphérique complexe et les interactions surface-atmosphère sur des terrains accidentés comme ceux du Maroc. L'expérience "T01" utilise le modèle RegCM pour simuler le climat, avec des résultats actuels couvrant la période de 1999 à 2000. Ce rapport technique synthétise les méthodes de calcul, les paramètres configurés, la volumétrie des sorties et les équations qui régissent certaines de ces interactions. L'objectif est de fournir un document de référence clair pour les utilisateurs de la simulation et les administrateurs du cluster de calcul.

---

# Description générale de la simulation

- **Nom de l'expérience** : T01
- **Domaine de simulation** : Maroc et ses environs
- **Période simulée** : 1er Janvier 1999 au 15 Novembre 2000
- **Modèle** : RegCM v4.5 (avec surface terrestre CLM45 active)
- **Environnement d'exécution** : Cluster Toubkal, nœuds de calcul (allocation CLIMAT-UM6P-ST-IWRI-7KSIFKVWKUY-DEFAULT-CPU)

La simulation intègre un maillage très fin pour résoudre les phénomènes à méso-échelle, tout en s'appuyant sur des réanalyses globales pour forcer ses frontières.

---

# Configuration et paramètres

Les paramètres géométriques et temporels du modèle sont définis dans les *namelists* `&dimparam`, `&geoparam` et `&timeparam` du fichier `test_0010.in`.

- **Dimensions de la grille** : 1084 (Longitude/jx) × 920 (Latitude/iy) × 50 (Niveaux verticaux/kz)
- **Résolution horizontale** : 3.0 km
- **Projection** : ROTLLR (Rotated Latitude-Longitude)
  - *Origine (Lat/Lon)* : 32.5° N / -12.5° E
  - *Pôle Nord de la grille (Lat/Lon)* : 57.5° N / 168.0° E
- **Pas de temps du modèle** : 30 secondes
- **Calendrier** : Grégorien

Le toit de l'atmosphère (`zita_height_top`) est fixé à 30 000 mètres.

---

# Conditions initiales et forçages

Le modèle nécessite des conditions aux frontières et des forçages océaniques pour contraindre la dynamique atmosphérique régionale.

## Forçages Atmosphériques (ICBC)
- **Source** : ERA5 (Réanalyse globale du CEPMMT)
- **Fréquence** : 6 heures
- **Variables principales forcées** : Pression de surface (`ps`), Température de surface (`ts`), Température de l'air (`t`), Humidité spécifique (`qv`), Vent Zonal/Méridien (`u`, `v`).
- **Volumétrie** : Environ 95 Go par fichier mensuel, ce qui nécessite une gestion attentive du stockage (`/ARCHIVE`).

## Forçage Océanique (SST)
- **Source** : ERA5
- **Variables forcées** : Température de Surface de la Mer (`sst`).
- La mise à jour régulière des SST permet de capturer l'influence thermique de l'océan Atlantique et de la mer Méditerranée sur le climat marocain.

## Surface Terrestre
Le modèle s'appuie sur des données statiques de type `LANDUSE` (utilisation des sols) et `TEXTURE` (texture du sol) préparées lors de la phase de pre-processing pour initier le modèle CLM45.

---

# Description détaillée des variables simulées

Les sorties de la simulation sont réparties en plusieurs flux (streams) temporels.

### Flux ATM (Atmosphère 3D) - Fréquence 6-heures
Variables tridimensionnelles (sur 50 niveaux verticaux).
- `ta` : Température de l'air [K]
- `ua`, `va`, `wa` : Composantes du vent (Est, Nord, Vertical) [m/s]
- `hus` : Humidité spécifique [kg/kg]
- Tendances radiatives et convectives : Ex. `ttenrad` (Tendance de température due au chauffage radiatif).

### Flux SRF (Surface) - Fréquence Horaire
Variables bidimensionnelles décrivant les échanges surface-atmosphère.
- `pr` : Précipitations [kg m-2 s-1]
- `ts` : Température de surface [K]
- `hfss`, `hfls` : Flux de chaleur sensible et latente [W m-2]
- `tas`, `uas`, `vas` : Température et vent proches de la surface [K, m/s]
- `mrro` : Ruissellement total [kg m-2 s-1]

### Flux RAD (Radiation) - Fréquence 6-heures
Variables liées aux bilans radiatifs (ondes courtes SW et ondes longues LW).
- `rsns`, `rsnl` : Flux radiatifs nets (Surface) [W m-2]
- `rsdt`, `rsut`, `rlut` : Flux radiatifs au sommet de l'atmosphère (TOA) [W m-2]
- `clt`, `clh`, `clm`, `cll` : Fractions nuageuses totales, hautes, moyennes et basses [%].

---

# Méthodes de calcul

RegCM résout numériquement les équations primitives atmosphériques en coordonnées sigma/zita. Voici quelques relations physiques fondamentales calculées par le modèle :

### 1. Bilan d'Énergie en Surface
Le modèle de surface (CLM) résout l'équilibre énergétique :
R_net = H + LE + G
Où R_net est la radiation nette, H est le flux de chaleur sensible (`hfss`), LE est le flux de chaleur latente (`hfls`) et G est le flux de chaleur dans le sol.

R_net = (SW_down - SW_up) + (LW_down - LW_up)
Où SW correspond aux ondes courtes (`rsns`) et LW aux ondes longues (`rsnl`).

### 2. Tendances de Température
Dans l'atmosphère (flux ATM), la variation temporelle de la température (`ta`) est la somme de plusieurs tendances radiatives, convectives et dynamiques :
dT/dt = ttenadh + ttenadv + ttentbl + ttendif + ttencon + ttenrad + ttenlsc
*(Advection horizontale, advection verticale, couche limite, diffusion, convection, rayonnement, grande échelle).*

### 3. Humidité Relative
Calculée à partir de l'humidité spécifique (`hus`), de la pression (`ps`) et de la température (`ta`).
e = (hus * ps) / (0.622 + 0.378 * hus)
RH = 100 * (e / e_s(T))
Où e_s(T) est la pression de vapeur saturante selon l'équation de Clausius-Clapeyron.

---

# Résultats et Analyse

*Note : Cette section décrit les capacités de la simulation basées sur l'analyse des variables. Aucune figure n'a pu être extraite des logs, l'analyse se concentre donc sur l'état du run.*

La configuration produit avec succès des variables atmosphériques détaillées. Le couplage avec CLM45 permet de suivre l'évolution de l'humidité du sol (`mrsol`) sur plusieurs couches, ce qui est crucial pour le Maroc (étude des sécheresses et de l'hydrologie).

Les flux horaires de surface (SRF) capturent le cycle diurne complet des vents (e.g. brises de mer) et des précipitations convectives (`pr`). Cependant, les flux 3D (ATM) limités à 6 heures lissent les processus convectifs profonds verticaux.

---

# Évaluation du stockage (Storage Assessment)

L'aspect critique de cette simulation réside dans la gestion massive des données générées (Big Data climatique).

### Empreinte actuelle
- **Durée simulée** : ~22.5 mois
- **Taille actuelle** : 27.13 To (Téraoctets)
- **Espace libre sur /srv/lustre01** : 2.2 To (Taux d'occupation global : 99.2% !)

### Répartition par flux
1. **ATM (6h)** : 25.7 GB/jour -> 64% du stockage total (~9.4 To/an)
2. **RAD (6h)** : 10.1 GB/jour -> 25% du stockage total (~3.7 To/an)
3. **SRF (1h)** : 2.76 GB/jour -> 7% du stockage total (~1.0 To/an)

### Projections de stockage
La poursuite de la simulation sans modification de fréquence nécessiterait un stockage brut proportionnel (environ 14.7 To par an de simulation).

---

# Discussion

La haute résolution (3 km) engendre des grilles de 1 million de points (920x1084) par niveau. Sur 50 niveaux verticaux, chaque variable 3D contient 50 millions de points. L'enregistrement de ces variables atmosphériques toutes les 6 heures sature le système de fichiers Lustre.

Il est paradoxal de constater que l'utilisateur dispose d'un budget CPU colossal de 1 000 000 d'heures, mais que la simulation sera physiquement stoppée (Erreur *No space left on device*) dans environ 1,5 mois de simulation en raison de l'espace disque.

---

# Limites de la simulation

1. **Volume de données** : Post-traiter des fichiers quotidiens ATM de 25 Go nécessitera des nœuds avec une mémoire RAM très importante. Le transfert réseau de 160 To est pratiquement impossible sans agrégation (CDO) préalable.
2. **Cycle Diurne 3D** : Un pas de temps de sortie à 6h pour le flux ATM empêche l'analyse du cycle diurne de la couche limite atmosphérique. Si l'on passe à 12h ou 24h pour économiser de l'espace, cette limite sera exacerbée.

---

# Conclusion

La simulation T01 de RegCM à 3 km sur le Maroc est correctement configurée et en cours d'exécution. Les choix paramétriques physiques (CLM45, ERA5) sont adéquats pour une étude climatologique fine. Néanmoins, l'expérience est confrontée à un mur matériel imminent. 

**Recommandations immédiates :**
1. **Nettoyage des archives** : Purger le dossier `ARCHIVE/` (178 To) et `TEMP/` (25 To) situés à la racine du projet qui saturent le système Lustre.
2. **Réduction de fréquence** : Dans `test_0010.in`, augmenter `atmfrq` et `radfrq` de 6h à 12h ou 24h. Cela permettrait d'économiser jusqu'à 9.3 To par an simulé (soit ~60% de gain total).

---

# Annexes

## Annexe A : Inventaire précis des fichiers
* Fichiers trouvés (ATM) : 685
* Fichiers de restart (SAV) : 25 (26 Go chacun). Il est conseillé de ne garder que le fichier SAV annuel (du 1er Janvier).

## Annexe B : Commandes utiles pour la gestion des données
* Pour lister l'utilisation disque : `lfs quota -u mohammad.elaabaribao /srv/lustre01`
* Pour agréger une variable spécifique sans saturer la RAM : `cdo selvar,tas,pr input.nc output.nc`
