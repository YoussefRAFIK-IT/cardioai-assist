# Architecture technique

```text
Navigateur
   │ HTTPS
   ▼
Flask + Gunicorn
   ├── Authentification / CSRF / contrôle d'accès
   ├── Parser ECG CSV/JSON/NPY
   ├── Rééchantillonnage 100 Hz et multi-segment
   ├── Ensemble RAW de cinq modèles Keras
   ├── Occlusion exploratoire
   ├── Rapport PDF
   └── SQLAlchemy
          │
          ▼
       PostgreSQL
```

Le modèle opérationnel est volontairement le RAW ensemble. La Late Fusion n'est pas déployée car ses poids ont été optimisés sur les OOF internes et elle n'a pas été validée extérieurement comme système complet.
