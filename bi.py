# -*- coding: utf-8 -*-
"""Bi.ipynb

Original file is located at
    https://colab.research.google.com/drive/13dcCEPz_uZRZe9SxRUshFDhpqnxxxFQD
"""

pip install pandas numpy matplotlib seaborn

#importer les packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

#charger le Dataset
df = pd.read_csv("PS_20174392719_1491204439457_log.csv")

print(f"Dataset chargé : {df.shape[0]:,} lignes | {df.shape[1]} colonnes")

df.head(5)

#description du jeu de donnee
df.describe()

# ÉTAPE 3 — DÉTECTION DES VALEURS MANQUANTES

missing = df.isnull().sum()
missing_pct = (missing / len(df)) * 100
missing_df = pd.DataFrame({
    'Valeurs manquantes': missing,
    'Pourcentage (%)': missing_pct.round(4)
})
print(missing_df)

# ÉTAPE 4 — DÉTECTION DES DOUBLONS

doublons = df.duplicated().sum()
print(f"Nombre de lignes dupliquées : {doublons}")

if doublons > 0:
    df = df.drop_duplicates()
    print(f"✔ Doublons supprimés. Nouveau shape : {df.shape}")
else:
    print("✔ Aucun doublon détecté.")

# ÉTAPE 5 — VÉRIFICATION DE LA COHÉRENCE DES SOLDES
# ─────────────────────────────────────────────────────────────
# Logique attendue : newbalanceOrig = oldbalanceOrg - amount
# Si ce n'est pas le cas → transaction suspecte

df['ecart_solde_emetteur'] = (
    df['oldbalanceOrg'] - df['amount'] - df['newbalanceOrig']
).round(2)

incoherences = df[df['ecart_solde_emetteur'].abs() > 1]
print(f"Transactions avec incohérence de solde : {len(incoherences):,}")
print(f"  → Dont frauduleuses : {incoherences['isFraud'].sum():,}")
print(f"  → Taux de fraude dans les incohérences : "
      f"{incoherences['isFraud'].mean()*100:.2f}%")

# Création d'un flag binaire d'incohérence
df['flag_incoherence_solde'] = (df['ecart_solde_emetteur'].abs() > 1).astype(int)

# ÉTAPE 6 — VÉRIFICATION DES VALEURS ABERRANTES (MONTANTS)

Q1 = df['amount'].quantile(0.25)
Q3 = df['amount'].quantile(0.75)
IQR = Q3 - Q1
borne_sup = Q3 + 3 * IQR  # seuil conservateur (3×IQR)

outliers = df[df['amount'] > borne_sup]
print(f"Seuil aberrant (Q3 + 3×IQR) : {borne_sup:,.2f}")
print(f"Nombre de montants aberrants : {len(outliers):,}")
print(f"  → Dont frauduleux : {outliers['isFraud'].sum():,}")

# Flag outlier (on ne les supprime pas — ils sont utiles pour la détection)
df['flag_montant_aberrant'] = (df['amount'] > borne_sup).astype(int)
print("✔ Flag 'flag_montant_aberrant' créé (1 = aberrant, 0 = normal).")

# ÉTAPE 7 — FILTRAGE : TYPES DE TRANSACTIONS PERTINENTS

print("Répartition de la fraude par type :")
print(df.groupby('type')['isFraud'].agg(['sum', 'mean']).rename(
    columns={'sum': 'Nb fraudes', 'mean': 'Taux fraude'}
))

types_fraude = ['TRANSFER', 'CASH_OUT']
df_fraude_focus = df[df['type'].isin(types_fraude)].copy()
print(f"\n✔ Sous-dataset TRANSFER + CASH-OUT : {df_fraude_focus.shape[0]:,} lignes")

# ÉTAPE 8 — CRÉATION DES VARIABLES DÉRIVÉES

# Heure de la journée (step % 24)
df['heure_jour'] = df['step'] % 24

# Jour de la simulation (step // 24)
df['jour_simulation'] = df['step'] // 24

# Ratio montant / solde initial de l'émetteur (évite division par zéro)
df['ratio_montant_solde'] = np.where(
    df['oldbalanceOrg'] > 0,
    df['amount'] / df['oldbalanceOrg'],
    0
)

# Le compte destinataire est-il un client (C) ou un marchand (M) ?
df['dest_est_client'] = df['nameDest'].str.startswith('C').astype(int)

# Solde émetteur vidé après la transaction ?
df['solde_vide_apres'] = (df['newbalanceOrig'] == 0).astype(int)

print("Variables créées :")
nouvelles_vars = ['heure_jour', 'jour_simulation', 'ratio_montant_solde',
                  'dest_est_client', 'solde_vide_apres']
print(df[nouvelles_vars].describe().round(3))

# ÉTAPE 9 — ENCODAGE DES VARIABLES CATÉGORIELLES

df['type_encoded'] = df['type'].astype('category').cat.codes
mapping = dict(enumerate(df['type'].astype('category').cat.categories))
print("Correspondance encodage :")
for code, label in mapping.items():
    print(f"  {code} → {label}")

# ÉTAPE 10 — RÉSUMÉ FINAL & EXPORT
# Colonnes à conserver pour la suite du projet
colonnes_finales = [
    'step', 'heure_jour', 'jour_simulation',
    'type', 'type_encoded',
    'amount', 'flag_montant_aberrant',
    'nameOrig', 'oldbalanceOrg', 'newbalanceOrig',
    'nameDest', 'dest_est_client', 'oldbalanceDest', 'newbalanceDest',
    'ecart_solde_emetteur', 'flag_incoherence_solde',
    'ratio_montant_solde', 'solde_vide_apres',
    'isFraud', 'isFlaggedFraud'
]

df_clean = df[colonnes_finales].copy()

print(f"Shape final du dataset nettoyé : {df_clean.shape}")
print(f"Colonnes : {list(df_clean.columns)}")
print(f"\nTaux de fraude final : {df_clean['isFraud'].mean()*100:.4f}%")

# Export du dataset nettoyé
df_clean.to_csv("paysim_clean.csv", index=False)
print("\n✔ Dataset nettoyé exporté → paysim_clean.csv")

# Re-créer df_fraude_focus pour inclure les nouvelles colonnes
types_fraude = ['TRANSFER', 'CASH_OUT']
df_fraude_focus_updated = df[df['type'].isin(types_fraude)].copy()

# Export du sous-dataset TRANSFER + CASH-OUT uniquement
df_fraude_focus_clean = df_fraude_focus_updated[colonnes_finales].copy()
df_fraude_focus_clean.to_csv("paysim_transfer_cashout.csv", index=False)
print(" Sous-dataset TRANSFER+CASH-OUT exporté → paysim_transfer_cashout.csv")

























