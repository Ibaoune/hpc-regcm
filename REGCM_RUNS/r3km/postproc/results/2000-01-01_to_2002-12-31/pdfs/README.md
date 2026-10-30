# Distributions et Extrêmes de Précipitation (PDFs) — Période 2000-01-01 au 2002-12-31

Ce répertoire contient l'analyse probabiliste des intensités de précipitation et des événements extrêmes simulés par **RegCM5 (~3 km)**, validés par rapport aux **stations météorologiques in-situ** et aux **réanalyses horaires ERA5**.

---

## 1. Description des Figures et Fichiers

### A. PDF Journalière Validée aux Stations In-Situ (`pr_daily_pdf_insitu_*.png`)
* **Figure principale** : Fonction de densité de probabilité (PDF, échelle logarithmique) des intensités journalières de pluie ($\ge 0.1\text{ mm/jour}$) sur l'ensemble de la période 2000–2002.
* **Encart (Inset)** : Zoom sur les faibles intensités ($0.1$ à $5.0\text{ mm/jour}$) en échelle linéaire.
* **Comparaison** :
  * Ligne noire continue : **Observations in-situ des stations ABH (186 stations retenues)**.
  * Ligne rouge/orange tiretée : **RegCM5 (~3 km extrait au point de grille le plus proche)**.
* **Tableau associé (`pr_station_intensity_*.csv`)** :
  * Nombre d'échantillons jours-stations appariés ($N = 202\text{ }262$)
  * Intensité moyenne des jours humides ($\ge 0.1\text{ mm/j}$)
  * 95ème percentile (**P95**) et 99ème percentile (**P99**)
  * Précipitation journalière maximale absolue (**Maximum**)

### B. PDF Horaire vs ERA5 (`pr_hourly_pdf_*.png`)
* `pr_hourly_pdf_native_resolution_*.png` : PDF calculée aux résolutions natives respectives (RegCM ~3 km vs ERA5 28 km).
* `pr_hourly_pdf_common_grid_*.png` : PDF après agrégation des mailles RegCM 3 km sur la grille commune ERA5 ($0.25^\circ$), permettant une comparaison géométrique équitable.

---

## 2. Méthodologie Détaillée de Calcul (Validation In-Situ)

### A. Données d'Observation In-Situ
* Source : Fichier centralisé des stations météorologiques des Agences de Bassins Hydrauliques (ABH) du Maroc (`ABH_stations_plusziz_and_abhbc1.csv`).
* Seuil de complétude temporelle : **$\ge 90\%$** sur les 1 096 jours de la période (les stations avec plus de 10% de lacunes sont exclues pour éviter les biais saisonniers).
* Nombre de stations retenues dans le domaine : **186 stations**.

### B. Appariement Spatial et Temporel
1. **Appariement spatial (Plus proche voisin géodésique)** :
   Pour chaque station de coordonnées $(\text{lon}_{\text{st}}, \text{lat}_{\text{st}})$, calcul de la distance orthodromique (Haversine) avec l'ensemble des points de grille 2D de RegCM :
   $$d = 2 R \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos\phi_1 \cos\phi_2 \sin^2\left(\frac{\Delta \lambda}{2}\right)} \right)$$
   Extraction de la maille RegCM $(i, j)$ minimisant $d$ (distance typique $< 2\text{ km}$).
2. **Cumul journalier harmonisé** :
   Les sorties horaires de RegCM sont cumulées de 00:00 à 23:00 UTC pour former les cumuls quotidiens correspondants.
3. **Appariement strict jour par jour** :
   Seules les paires $(\text{Obs}(d, s), \text{RegCM}(d, s))$ où ni l'observation ni le modèle n'est manquant sont conservées (total de 202 262 couples jour-station).

### C. Calcul de la Fonction de Densité de Probabilité (PDF)
* La distribution n'est calculée que sur les **jours humides** ($P \ge 0.1\text{ mm/jour}$).
* Les histogrammes sont normalisés en densité de probabilité telle que :
  $$\int_{0.1}^{\infty} f(p) \, dp = 1$$
* L'axe vertical est logarithmique pour mettre en évidence la queue de distribution des événements extrêmes rares.

---

## 3. Guide d'Interprétation

* **Effet d'échelle (Point vs Maille)** : Une station pluviométrique mesure une pluie ponctuelle à l'entonnoir ($< 1\text{ m}^2$), alors qu'une cellule de modèle représente la moyenne spatiale sur une boîte de $\approx 9\text{ km}^2$. Il est donc physique que les maxima ponctuels des stations ($360\text{ mm/j}$) soient plus élevés que le maximum surfacique de maille de RegCM ($117\text{ mm/j}$).
* **Comportement du modèle convection-permitting (3 km)** :
  * Capture fidèlement la pente de décroissance de la PDF jusqu'au P99 ($30\text{ mm/j}$).
  * Évite le problème classique du *"drizzle effect"* (bruine permanente irréaliste) typique des modèles climatiques globaux à convection paramétrée.
