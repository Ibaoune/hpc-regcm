# Cartes Climatologiques — Période 2000-01-01 au 2002-12-31

Ce répertoire contient les cartes d'évaluation spatiale de la simulation **RegCM5 (~3 km convection-permitting)** comparée aux produits d'observations et réanalyses de référence sur l'ensemble du Maroc.

---

## 1. Description des Figures et Conventions de Nommage

Deux types d'agencements graphiques sont générés :

1. **Cartes Saisonnières (`*_seasonal_*.png`)** :
   - Grille de **3 lignes × 4 colonnes** couvrant les 4 saisons standards :
     - **DJF** : Décembre – Janvier – Février (Hiver)
     - **MAM** : Mars – Avril – Mai (Printemps)
     - **JJA** : Juin – Juillet – Août (Été)
     - **SON** : Septembre – Octobre – Novembre (Automne)
   - **Ligne 1** : Référence observationnelle sélectionnée (Observation)
   - **Ligne 2** : Modèle RegCM5 (~3 km rééchantillonné sur la grille commune)
   - **Ligne 3** : Biais absolu ($\text{Biais} = \text{RegCM} - \text{Obs}$)
   - **Encarts métriques** : Sur chaque panneau de biais sont affichés le biais moyen spatial ($\text{MB}$), la racine de l'erreur quadratique moyenne spatiale ($\text{RMSE}$) et le coefficient de corrélation spatiale de Pearson ($r$).

2. **Cartes Période Moyenne (`*_period_*.png`)** :
   - Agencement **1 ligne × 3 colonnes** (Moyenne globale sur les 3 ans, du 1er janvier 2000 au 31 décembre 2002) :
     - (a) Observation | (b) RegCM (~3 km) | (c) Biais absolu ($\text{Modèle} - \text{Obs}$)

---

## 2. Jeux de Données de Référence

* **Précipitations (`pr`)** :
  * **`MSWEP` (v2.8)** : Produit multi-sources haute résolution ($0.1^\circ \approx 10\text{ km}$) fusionnant jauges pluviométriques au sol, données satellitaires (IR/micro-ondes) et réanalyses. C'est la référence d'or pour la pluie en zone à orographie complexe.
  * **`EUR-12` (ICTP RegCM5 CORDEX-CORE)** : Simulation indépendante à $12\text{ km}$ ($0.11^\circ$) forcée par EC-Earth3-Veg. Permet d'évaluer la **valeur ajoutée de la résolution 3 km convection-permitting** par rapport au 12 km conventionnel.
* **Températures (`tasmax`, `tasmin`)** :
  * **`CPC` (NOAA Climate Prediction Center Global Daily)** : Grille interpolée d'observations de stations au sol à $0.5^\circ$.
  * **`EUR-12`** : Simulation CORDEX à $12\text{ km}$.

---

## 3. Méthodologie de Calcul

### A. Agrégation temporelle
* **Pour chaque jour $d$** :
  * Précipitations : Somme journalière ou flux converti en mm/jour.
  * Températures : Maximum journalier (`tasmax`) et minimum journalier (`tasmin`) en °C.
* **Moyenne saisonnière** :
  $$\bar{X}_{\text{saison}}(i, j) = \frac{1}{N_{\text{jours}}} \sum_{d \in \text{saison}} X(i, j, d)$$
  où $N_{\text{jours}}$ regroupe tous les jours de la saison sur les 3 années 2000, 2001 et 2002.
* **Moyenne de période (Annuelle)** :
  $$\bar{X}_{\text{période}}(i, j) = \frac{1}{1095} \sum_{d=1}^{1095} X(i, j, d)$$

### B. Harmonisation spatiale et Regridding
* Les sorties natives RegCM (~3 km non-hydrostatique) et les observations possèdent des résolutions et des projections différentes.
* **Algorithme de regridding** (via `xESMF` / `ESMF`) :
  * **Précipitations (`pr`)** : Regridding **conservatif** de premier ordre (`conservative`), garantissant la stricte conservation de la masse d'eau entre la grille fine 3 km et la grille cible de l'observation.
  * **Températures (`tasmax`, `tasmin`)** : Interpolation **bilinéaire** (`bilinear`) avec masquage cohérent terre/mer.
* **Masque géographique** : Délimitation sur les frontières officielles unifiées du Maroc (incluant les provinces sahariennes) via la base Natural Earth 50m.

---

## 4. Guide d'Interprétation

* **Orographie et Précipitations** : RegCM à 3 km résout explicitement les barrières orographiques (Rif, Moyen Atlas, Haut Atlas, Anti-Atlas). On observe une intensification réaliste des pluies sur les versants au vent (façade atlantique/méditerranéenne) et un assèchement sous le vent (ombres pluviométriques dans le Souss et le versant présaharien).
* **Gradient thermique altimétrique (Lapse Rate)** : Les températures maximales et minimales épousent fidèlement les crêtes atlasiques, avec des gradients verticaux plus raides et réalistes que dans les produits maillés grossiers.
