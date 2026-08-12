# Statut V1 — Deployment Ready

Validé avant création de cette release :
- bundle réel 5 modèles + 10 scalers ;
- reproduction OOF PTB-XL ;
- pipeline externe PTBDB exact ;
- parcours Flask E2E réel : 3/3 ECG externes ;
- SQL / historique / administration / PDF ;
- XAI applicative : lead + temporal occlusion sur ECG PTBDB externe.

Correctifs production ajoutés :
- dialecte PostgreSQL psycopg3 ;
- web service Render Standard (2 GB RAM) ;
- variables TensorFlow/OMP prudentes ;
- warm-up protégé par API key ;
- smoke test post-déploiement ;
- Gunicorn 1 worker / 2 threads.

À prouver après déploiement :
- URL HTTPS publique ;
- PostgreSQL Render connecté ;
- health check 200 ;
- warm-up réussi ;
- analyse réelle depuis l'URL publique ;
- tests Chrome / Edge / Firefox ;
- captures finales.
