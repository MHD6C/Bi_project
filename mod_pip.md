# Pipeline BI pour la détection de fraudes financières

## 1. Objectif du projet

L’objectif est de construire un pipeline BI complet permettant d’analyser des transactions financières et de détecter des comportements frauduleux.  
À partir d’un fichier CSV contenant des transactions simulées (`paysim_clean.csv`), nous mettons en place :

- un **modèle en étoile** (star schema) avec tables de faits et dimensions,
- un **data warehouse** relationnel (SQLite),
- un **cube OLAP** via des vues matérialisées,
- des **indicateurs de mesure** (volume, anomalies, taux de fraude).

L’ensemble est automatisé par un script Python unique.

---

## 2. Architecture du pipeline

[CSV brut] → [Nettoyage & transformation] → [Dimensions + Fait] → [Data Warehouse SQLite] → [Vues OLAP] → [Export CSV / Analyse]


### Technologies utilisées

- **Python 3** avec les bibliothèques : `pandas`, `sqlite3`, `os`
- **SQLite** comme entrepôt de données (Data Warehouse)
- **Vues SQL** pour le cube OLAP
- **Export CSV** pour alimenter des outils de visualisation (Power BI, Tableau)

---

## 3. Modélisation en étoile (Star Schema)

Le modèle en étoile est composé d’une table de fait centrale et de plusieurs tables de dimensions.

### 3.1 Table de fait : `Fait_Transaction`

| Colonne | Type | Description |
|---------|------|-------------|
| `id_transaction` | INTEGER | Clé primaire |
| `id_temps` | INTEGER | Clé étrangère vers `Dim_Temps` |
| `id_type` | INTEGER | Clé étrangère vers `Dim_Type_Transaction` |
| `id_emetteur` | INTEGER | Clé étrangère vers `Dim_Client` (compte source) |
| `id_destinataire` | INTEGER | Clé étrangère vers `Dim_Client` (compte destination) |
| `amount` | REAL | Montant de la transaction |
| `oldbalanceOrg`, `newbalanceOrig` | REAL | Soldes avant/après de l’émetteur |
| `oldbalanceDest`, `newbalanceDest` | REAL | Soldes avant/après du destinataire |
| `isFraud`, `isFlaggedFraud` | INTEGER | Flags de fraude (0/1) |
| `ratio_montant_solde` | REAL | `amount / oldbalanceOrg` (anomalie si >1) |
| `ecart_solde_emetteur` | REAL | Différence de solde |
| `flag_incoherence_solde` | INTEGER | Incohérence détectée |
| `solde_vide_apres` | INTEGER | Solde émetteur = 0 après transaction |
| `flag_montant_aberrant` | INTEGER | Montant anormal selon règle métier |

### 3.2 Dimensions

#### `Dim_Temps`

| Colonne | Type | Description |
|---------|------|-------------|
| `id_temps` | INTEGER | Clé primaire |
| `step` | INTEGER | Pas de temps (unité de la simulation) |
| `heure_jour` | INTEGER | Heure de la journée (0-23) |
| `jour_simulation` | INTEGER | Jour de simulation |
| `tranche_horaire` | TEXT | Catégorie : `nuit`, `matin`, `apres-midi`, `soir` |

#### `Dim_Type_Transaction`

| Colonne | Type | Description |
|---------|------|-------------|
| `id_type` | INTEGER | Clé primaire |
| `type` | TEXT | Type : `PAYMENT`, `TRANSFER`, `CASH_OUT`, `DEBIT`, `CASH_IN` |
| `type_encoded` | INTEGER | Code numérique associé |
| `categorie` | TEXT | Regroupement : `sortant`, `entrant`, `interne`, `autre` |

#### `Dim_Client`

| Colonne | Type | Description |
|---------|------|-------------|
| `id_client` | INTEGER | Clé primaire |
| `name` | TEXT | Identifiant du compte (`nameOrig` ou `nameDest`) |
| `est_client_banque` | INTEGER | 1 si le compte a déjà été destinataire avec `dest_est_client=1` |

---

## 4. Création du Data Warehouse (SQLite)

Le script Python :

1. **Nettoie et type** les colonnes du CSV.
2. **Construit** les DataFrames pour chaque dimension et la table de fait.
3. **Crée** une base SQLite (`datawarehouse.db`) et les tables SQL correspondantes avec clés primaires/étrangères.
4. **Insère** les données.
5. **Ajoute des index** pour accélérer les requêtes (sur les clés étrangères). 


Exemple de création de table :

   sql
CREATE TABLE Fait_Transaction (
    id_transaction INTEGER PRIMARY KEY,
    id_temps INTEGER,
    id_type INTEGER,
    id_emetteur INTEGER,
    id_destinataire INTEGER,
    amount REAL,
    ...
    FOREIGN KEY (id_temps) REFERENCES Dim_Temps(id_temps),
    FOREIGN KEY (id_type) REFERENCES Dim_Type_Transaction(id_type),
    FOREIGN KEY (id_emetteur) REFERENCES Dim_Client(id_client),
    FOREIGN KEY (id_destinataire) REFERENCES Dim_Client(id_client)
); 

## 5. Cube OLAP (vues matérialisées)
Bien que SQLite ne soit pas un serveur OLAP dédié, le script simule un cube multidimensionnel à l’aide de vues SQL qui agrègent les données selon plusieurs axes et niveaux de granularité.

### 5.1 Vue Cube_Fraude_Type_Temps
Agrège les fraudes par :

type de transaction (avec total 'Tous')

tranche horaire (avec total 'Toutes')

Utilise des UNION ALL pour reproduire l’effet d’un ROLLUP.
Mesures : nombre de transactions, nombre de fraudes, taux de fraude (%), montant total, montant moyen.

### 5.2 Vue Anomalies_Par_Emetteur

Pour chaque émetteur, calcule :

nombre total de transactions,

nombre de fraudes,

nombre de dépassements de solde (ratio > 1),

nombre d’incohérences de solde,

nombre de soldes vidés après transfert,

montant total émis et montant moyen.

### 5.3 Vue Anomalies_Par_Destinataire

Pour chaque destinataire, calcule :

transactions reçues,

fraudes associées,

montants aberrants reçus,

montant total et moyen reçu.

### 5.4 Vue Evolution_Fraude_Temporelle

Suit l’évolution des fraudes dans le temps (step et tranche horaire).

### 6. Structuration des mesures
Les mesures sont organisées selon trois axes principaux :

Axe	Mesures typiques
Volume	nb_transactions, montant_total, montant_moyen
Fraude	nb_fraudes, taux_fraude_pct, montant_total_fraudes
Anomalies	nb_ratio_depassement, nb_incoherence_solde, nb_solde_vide, nb_montants_aberrants
Ces mesures sont calculées :

dans les vues OLAP,

dans les requêtes d’indicateurs globaux,

exportées dans des fichiers CSV pour une visualisation externe.

Exemple de requête d’indicateurs globaux :

SELECT 
    COUNT(*) AS total_transactions,
    SUM(isFraud) AS total_fraudes,
    ROUND(100.0 * SUM(isFraud) / COUNT(*), 2) AS taux_fraude_global,
    ROUND(SUM(amount), 2) AS montant_total,
    ROUND(AVG(amount), 2) AS montant_moyen,
    SUM(CASE WHEN ratio_montant_solde > 1 THEN 1 ELSE 0 END) AS transactions_ratio_superieur_1,
    SUM(flag_incoherence_solde) AS incoherences_solde,
    SUM(solde_vide_apres) AS soldes_vides_apres_transfert
FROM Fait_Transaction;

## 7. Exemples de requêtes d’analyse

### 7.1 Taux de fraude par type de transaction

SELECT t.type, t.categorie,
       COUNT(*) AS nb,
       SUM(f.isFraud) AS fraudes,
       ROUND(100.0 * SUM(f.isFraud) / COUNT(*), 2) AS taux
FROM Fait_Transaction f
JOIN Dim_Type_Transaction t ON f.id_type = t.id_type
GROUP BY t.type;

### 7.2 Top 10 des émetteurs frauduleux

SELECT c.name, COUNT(*) AS total, SUM(f.isFraud) AS fraudes
FROM Fait_Transaction f
JOIN Dim_Client c ON f.id_emetteur = c.id_client
GROUP BY c.id_client
ORDER BY fraudes DESC
LIMIT 10;

### 7.3 Transactions suspectes (ratio montant/solde > 2)

sql
SELECT f.id_transaction, t.type, f.amount, f.oldbalanceOrg, f.ratio_montant_solde
FROM Fait_Transaction f
JOIN Dim_Type_Transaction t ON f.id_type = t.id_type
WHERE f.ratio_montant_solde > 2
ORDER BY f.ratio_montant_solde DESC;

## 8. Exécution du pipeline

Prérequis
Python 3.7+

Bibliothèques : pandas, sqlite3 (incluse dans Python)

Étapes
Placer le fichier paysim_clean.csv dans le même répertoire que le script.

Exécuter le script dans le terminal:

python pipeline_fraude.py

Le script génère :

datawarehouse.db : base de données SQLite contenant le schéma en étoile.

Quatre fichiers CSV : cube_fraude_type_temps.csv, anomalies_emetteurs.csv, anomalies_destinataires.csv, evolution_fraude_temps.csv.

Les résultats sont affichés dans la console (indicateurs globaux, top émetteurs, etc.).

Visualisation
Les fichiers CSV exportés peuvent être chargés dans Power BI, Tableau ou Excel pour créer des tableaux de bord interactifs.

## 9. Conclusion
Le pipeline BI mis en place répond aux exigences de modélisation en étoile, de création d’un data warehouse, de mise en place d’un cube OLAP et de structuration des mesures. Il permet une analyse multidimensionnelle efficace des transactions et une détection proactive des fraudes.

Le code est modulaire, documenté et facilement adaptable à d’autres jeux de données financiers.

