 Bi_project — Analyse des Transactions Financières

Détection de fraude sur le dataset PaySim | Projet Business Intelligence


Objectif du projet
Détecter des transactions financières frauduleuses à partir d'un dataset de paiements mobiles simulés (PaySim), en combinant nettoyage de données, modélisation BI, analyse MDX et dashboard de visualisation.

👥 Répartition des tâches
MembreRôleResponsabilitésPersonne 1DonnéesNettoyage, exploration, variables dérivéesPersonne 2Modélisation BIModèle en étoile, data warehouse, cube OLAPPersonne 3Analyse MDXRequêtes MDX, détection d'anomaliesPersonne 4DashboardVisualisations, storytelling, présentation finale

 Structure du repository
Bi_project/
│
├── bi.py                        
├── README.md                    
│
└── (à venir)
    ├── modele_etoile/           # Kamil Diaw — modèle BI
    ├── requetes_mdx/            # Maimouna Sow — requêtes MDX
    └── dashboard/               # Mame Seynabou Ndiaye — dashboard final

 Dataset
PaySim — Synthetic Financial Datasets for Fraud Detection

 Source : kaggle.com/datasets/ealaxi/paysim1
 Fichier : PS_20174392719_1491204439457_log.csv
 Taille : 6 362 620 transactions | 11 colonnes
 Période : 30 jours simulés (744 heures)
 Taux de fraude : 0,13% (8 213 transactions frauduleuses)


 Travail réalisé — Mohamed Cisse
Le script bi.py effectue les étapes suivantes :

Chargement du dataset brut
Exploration initiale (types, distributions, taux de fraude)
Valeurs manquantes — vérification colonne par colonne → aucune détectée
Doublons — détection et suppression → aucun détecté
Cohérence des soldes — vérification : oldbalanceOrg - amount = newbalanceOrig
Valeurs aberrantes — méthode IQR sur les montants (seuil : Q3 + 3×IQR)
Filtrage — isolation des types TRANSFER et CASH-OUT (seuls types avec fraude)
Variables dérivées — création de 7 nouvelles features :

heure_jour — heure dans la journée (0–23)
jour_simulation — numéro du jour (0–30)
ratio_montant_solde — part du solde dépensée en une transaction
dest_est_client — destinataire client (1) ou marchand (0)
solde_vide_apres — compte vidé après la transaction
flag_incoherence_solde — incohérence comptable détectée
flag_montant_aberrant — montant statistiquement hors norme


Encodage — conversion de la colonne type en numérique (type_encoded)
Export — génération des fichiers CSV nettoyés

