# CardioAI Assist — V1 Final Candidate

Plateforme web Data & IA développée dans le cadre d'un stage de PFE Master. Elle centralise l'import, le contrôle, la visualisation, l'inférence, la traçabilité et l'explicabilité exploratoire d'ECG 12 dérivations pour la tâche **MI versus strict NORM**.

## Pipeline réellement intégré

- RAW InceptionTime-SE, 5 modèles ;
- 502 497 paramètres par modèle ;
- normalisation fold-wise ;
- entrée 1000 × 12 à 100 Hz ;
- cinq fenêtres pour un ECG long : début, 25 %, centre, 75 %, fin ;
- moyenne des modèles puis des fenêtres ;
- seuil interne verrouillé : 0,72 ;
- aucune Late Fusion dans l'application.

## Validation

**PTB-XL OOF patient-wise (RAW)** : ROC-AUC 0,9778 ; PR-AUC 0,9670 ; Accuracy 0,9263 ; Sensibilité 0,8879 ; Spécificité 0,9494 ; F1 0,9006 ; Brier 0,0594.

**PTBDB, pipeline exact de l'application, niveau patient** : N=200 ; ROC-AUC 0,9461 ; PR-AUC 0,9824 ; Accuracy au seuil 0,72 = 0,6600 ; Sensibilité 0,5405 ; Spécificité observée 1,0000 ; F1 0,7018 ; Brier 0,1133 ; ECE10 0,1366.

La forte discrimination externe n'implique pas une bonne transportabilité du seuil. Le prototype n'est pas un dispositif médical.

## Fonctions V1

- authentification et rôles analyste/admin ;
- back-office administrateur ;
- import CSV/JSON/NPY ;
- contrôle des 12 dérivations, NaN/Inf, durée et fréquence ;
- rééchantillonnage à 100 Hz ;
- multi-segment exact ;
- vraie inférence sur 5 modèles ;
- aucune bascule silencieuse vers le mode synthétique ;
- visualisation Plotly ;
- occlusion lead/temporelle optionnelle ;
- historique SQL et journal d'audit ;
- PDF ;
- API REST ;
- SQLite local / PostgreSQL production ;
- Docker / Render ;
- exemples externes PTBDB.

## Installation locale

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
python scripts/verify_model_bundle.py
python scripts/smoke_test_real_inference.py
python run.py
```

Ouvrir `http://127.0.0.1:5000`.

## Variables obligatoires avant présentation

- `SECRET_KEY`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `API_KEY`
- `DEMO_MODE=false`
- `MODEL_THRESHOLD=0.72`
- `MODEL_VERSION=raw-inceptiontime-se-nested-v1`

En mode réel, un bundle invalide bloque l'inférence. `DEMO_SYNTHETIC` n'est possible que si `DEMO_MODE=true` a été choisi explicitement.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Puis suivre `docs/RECETTE_V1.md`.

## Déploiement

Le `Dockerfile`, `docker-compose.yml` et `render.yaml` sont fournis. L'application utilise un seul worker Gunicorn afin d'éviter de charger cinq modèles TensorFlow dans plusieurs processus.

Avant la soutenance, produire les preuves réelles : URL HTTPS, `/api/v1/health`, logs, captures multi-navigateurs et dump PostgreSQL.
