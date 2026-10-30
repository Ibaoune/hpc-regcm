# Cycle Diurne — Période 2000-01-01 au 2002-12-31

Ce répertoire regroupe les diagnostics de validation du **cycle diurne de la température à 2 m (`tas`)**, comparant la simulation **RegCM5 (~3 km)** aux réanalyses horaires **ERA5 ($0.25^\circ \approx 28\text{ km}$)** du CEPMMT (ECMWF).

---

## 1. Description des Figures

### A. Courbes Diurnes Nationales (`tas_diurnal_cycle_curves_*.png`)
* **Figure à 5 panneaux** montrant l'évolution heure par heure de 00:00 à 23:00 UTC pour :
  * **Annual** (Annuel complet sur 1 095 jours)
  * **DJF** (Hiver)
  * **MAM** (Printemps)
  * **JJA** (Été)
  * **SON** (Automne)
* **Courbes** :
  * Ligne orange continue avec ronds : **RegCM5 (3 km)**
  * Ligne bleue tiretée avec carrés : **ERA5 (horaire)**
* **Encart d'évaluation** sur chaque panneau :
  * Heure de pic du modèle (`Peak Mod` en UTC)
  * Heure de pic d'ERA5 (`Peak ERA5` en UTC)
  * Déphasage ($\Delta t = \text{Pic Mod} - \text{Pic Obs}$ en heures)
  * Biais d'amplitude diurne ($\text{Amp Bias}$ en °C)

### B. Cartes Spatiales de l'Heure de Pic (`tas_diurnal_peak_hour_*.png`)
* Agencement **1 ligne × 3 cartes** (généré pour Annuel, JJA et DJF) :
  * **(a) Heure de pic ERA5** (colormesh cyclique 0h à 24h UTC)
  * **(b) Heure de pic RegCM** (rééchantillonné sur la grille ERA5 via KDTree)
  * **(c) Différence de phase** ($\text{RegCM} - \text{ERA5}$, de $-6\text{h}$ à $+6\text{h}$)

### C. Cartes Spatiales de l'Amplitude Diurne (`tas_diurnal_amplitude_*.png`)
* Agencement **1 ligne × 3 cartes** :
  * **(a) Amplitude diurne ERA5** ($T_{\max} - T_{\min}$ en °C)
  * **(b) Amplitude diurne RegCM** ($T_{\max} - T_{\min}$ en °C)
  * **(c) Biais d'amplitude** ($\text{RegCM} - \text{ERA5}$ en °C)

---

## 2. Méthodologie et Formules de Calcul

### A. Calcul des Courbes Diurnes (Moyennage Spatial puis Temporel)
1. **Extraction spatiale** : Pour chaque heure UTC $h \in \{0, 1, \dots, 23\}$ de chaque jour :
   $$T_{\text{spatial}}(h, \text{jour}) = \frac{1}{N_{\text{points}}} \sum_{(x, y) \in \text{Maroc}} T(h, x, y, \text{jour})$$
2. **Agrégation temporelle** : Moyenne sur l'ensemble des jours de la saison ou de la période :
   $$\bar{T}(h) = \frac{1}{N_{\text{jours}}} \sum_{\text{jour}} T_{\text{spatial}}(h, \text{jour})$$
3. **Traitement de l'heure 00:00 UTC d'ERA5** :
   Les fichiers bruts d'ERA5 ne contenant que les pas de temps de 01:00 à 23:00 UTC (heure 00:00 omise lors de l'extraction CDS d'origine), l'heure 00:00 UTC d'ERA5 est interpolée linéairement entre 23:00 UTC et 01:00 UTC :
   $$\text{ERA5}(00\text{h}) = \frac{\text{ERA5}(23\text{h}) + \text{ERA5}(01\text{h})}{2}$$
   Cela garantit une onde thermique nocturne physiquement continue sans saut artificiel à 0 °C.

### B. Calcul des Métriques
* **Amplitude diurne** :
  $$\text{Amplitude} = \max_{h} \bar{T}(h) - \min_{h} \bar{T}(h)$$
* **Biais d'amplitude** :
  $$\text{Biais}_{\text{amp}} = \text{Amplitude}_{\text{RegCM}} - \text{Amplitude}_{\text{ERA5}}$$
* **Différence de phase** (déphasage cyclique sur 24h) :
  $$\Delta t = (h_{\text{pic, RegCM}} - h_{\text{pic, ERA5}} + 12) \pmod{24} - 12$$

---

## 3. Pourquoi la Précipitation est Exclue du Cycle Diurne National

Contrairement à la température (qui suit un cycle forcé par le rayonnement solaire partout), la précipitation au Maroc est dominée en hiver, automne et printemps par des **systèmes frontaux atlantiques stochastiques** qui traversent le pays à toute heure du jour ou de la nuit. Moyenner la pluie sur 24h et sur tout le pays donne une courbe plate et sans pertinence physique. La dynamique convective estivale locale est quant à elle analysée via les distributions et quantiles extrêmes dans le répertoire `pdfs/`.
