# Déploiement Render — V1

## Choix d'instance

Pour la soutenance, le Blueprint utilise un **web service Standard (2 GB RAM, 1 CPU)**.
Le modèle TensorFlow charge cinq réseaux Keras ; 512 MB (Free/Starter) est considéré trop risqué
pour une démonstration stable. La base PostgreSQL reste en `basic-256mb`, suffisante pour le faible
volume de données du prototype.

## Avant le déploiement

1. Pousser tout le contenu de ce dossier à la racine d'un dépôt GitHub privé.
2. Vérifier que `models/` est bien versionné et contient les 15 artefacts + `model_manifest.json`.
3. Ne jamais committer `.env`.
4. Sur Render : **New > Blueprint**, connecter le dépôt et utiliser `render.yaml`.
5. Renseigner manuellement :
   - `ADMIN_EMAIL`
   - `ADMIN_PASSWORD`
6. Render génère automatiquement :
   - `SECRET_KEY`
   - `API_KEY`
7. La base `cardioai-db` est créée dans la même région (`frankfurt`).

## Vérifications après déploiement

- Ouvrir `/api/v1/health` : doit répondre HTTP 200 et `REAL_RAW_ENSEMBLE`.
- Récupérer la valeur `API_KEY` dans Render.
- Depuis un terminal :

```bash
python scripts/post_deploy_smoke_test.py \
  --base-url https://VOTRE-SERVICE.onrender.com \
  --api-key "VOTRE_API_KEY" \
  --warmup
```

Le warm-up charge les cinq modèles et compile une première passe technique. La probabilité issue du
tenseur nul est jetée et n'est jamais stockée ni affichée.

## Démonstration jury

Avant la présentation :
1. appeler le warm-up ;
2. se connecter ;
3. analyser `sample_data/public_demo/ptbdb_demo_healthy_correct.csv` ;
4. analyser `ptbdb_demo_mi_correct.csv` ;
5. garder `ptbdb_demo_borderline_correct.csv` pour montrer le seuil et, si nécessaire, l'XAI.

## Point PostgreSQL corrigé

Render fournit `DATABASE_URL` sous forme `postgresql://...`.
Le code convertit désormais explicitement cette URL vers le dialecte SQLAlchemy
`postgresql+psycopg://...`, cohérent avec la dépendance `psycopg[binary]`.
