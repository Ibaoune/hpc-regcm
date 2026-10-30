# Résultats d'Évaluation Post-Traitement RegCM5 (~3 km) — Période 2000–2002

Ce répertoire rassemble l'ensemble des diagnostics de validation et d'évaluation climatologique de la simulation **RegCM5 non-hydrostatique à résolution convective (~3 km)** sur le domaine du Maroc pour la période triennale du **01/01/2000 au 31/12/2002 (1 095 jours de simulation)**.

---

## 1. Structure du Répertoire

```text
2000-01-01_to_2002-12-31/
├── maps/       # Cartes spatiales climatologiques (période et saisonnières)
├── diurnal/    # Cycle diurne de la température à 2 m (courbes et cartes 2D)
├── pdfs/       # Distributions de précipitation (PDF horaire ERA5 et quotidienne in-situ)
└── metrics/    # Tables quantitives de synthèse au format CSV
```

---

## 2. Synthèse des Diagnostics Disponibles

| Répertoire | Variables | Données de Référence | Type de Diagnostic | Objectif Scientifique |
| :--- | :--- | :--- | :--- | :--- |
| **`maps/`** | `pr`, `tasmax`, `tasmin` | MSWEP v2.8 ($0.1^\circ$), CPC ($0.5^\circ$), EUR-12 CORDEX ($12\text{ km}$) | Cartes saisonnières (DJF, MAM, JJA, SON) et moyenne triennale | Évaluation de la répartition spatiale, du blocage orographique et des contrastes thermiques. |
| **`diurnal/`** | `tas` (température à 2 m) | ERA5 horaire ($0.25^\circ$) | Courbes horaires 00h–23h UTC et cartes spatiales de pic/amplitude | Validation de l'onde thermique radiatif, de la phase diurne et de l'amplitude jour/nuit. |
| **`pdfs/`** | `pr` (précipitation) | 186 stations au sol ABH, ERA5 horaire | PDF logarithmique et percentiles extrêmes (P95, P99, Max) | Vérification de la distribution des intensités pluvieuses et capture des événements torrentiels. |
| **`metrics/`** | Toutes | MSWEP, CPC, EUR-12, ERA5, Stations | Fichiers `.csv` structurés | Métriques numériques (biais, RMSE, corrélation spatiale, déphasage diurne). |

---

## 3. Guide de Lecture Rapide de chaque Répertoire

Pour les détails d'implémentation, les formules mathématiques exactes et le protocole d'appariement, veuillez consulter les README dédiés dans chaque sous-dossier :
* [`maps/README.md`](maps/README.md)
* [`diurnal/README.md`](diurnal/README.md)
* [`pdfs/README.md`](pdfs/README.md)
