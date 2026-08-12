# Données de démonstration

Les exemples `public_demo/` proviennent de **PTB Diagnostic ECG Database (PTBDB)**, un dataset externe qui n'a pas servi à entraîner les cinq modèles RAW.

- `ptbdb_demo_healthy_correct.*` : contrôle sain correctement classé.
- `ptbdb_demo_mi_correct.*` : MI correctement classé.
- `ptbdb_demo_borderline_correct.*` : MI correctement classé avec une probabilité proche du seuil 0,72.

Le dossier `report_only/` contient un cas d'erreur proche du seuil, conservé uniquement pour l'analyse des limites dans le mémoire et la soutenance. Il ne doit pas être présenté comme une réussite du modèle.

Les fichiers ne contiennent aucune identité nominative. Les métadonnées de sélection sont dans `external_demo_ecg_metadata.csv`.
