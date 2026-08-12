# Bundle modèle réel validé

Ce dossier contient le bundle RAW InceptionTime-SE validé :

- 5 modèles Keras (`nested_gpu_inceptiontime_se_outer1..5.keras`) ;
- 5 moyennes fold-wise ;
- 5 écarts-types fold-wise ;
- `model_manifest.json` avec les empreintes SHA-256.

Commande de contrôle :

```bash
python scripts/verify_model_bundle.py
```

En `DEMO_MODE=false`, l'application refuse toute inférence si le manifeste, un hash, un scaler, une forme ou la version ne sont pas cohérents. Il n'existe aucun fallback silencieux vers le mode synthétique.
