# Guide de déploiement pas à pas — CardioAI Assist V1

## 1. Principe de sécurité

La version finale est configurée pour le **pipeline réel** (`DEMO_MODE=false`). Le bundle de 15 artefacts est déjà inclus dans `models/`.

Le mode synthétique n'est conservé que pour des tests explicites d'interface. En mode réel, si le bundle est absent, altéré ou incohérent, l'inférence est bloquée : l'application ne revient jamais silencieusement vers `DEMO_SYNTHETIC`.

## 2. Installation locale Windows

1. Installer Python 3.11.
2. Décompresser le projet.
3. Ouvrir PowerShell dans le dossier du projet.
4. Créer l'environnement : `py -3.11 -m venv .venv`.
5. Activer : `.venv\\Scripts\\Activate.ps1`.
6. Installer : `pip install -r requirements.txt`.
7. Copier `.env.example` vers `.env`.
8. Renseigner au minimum `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` et `API_KEY`.
9. Vérifier `DEMO_MODE=false`.
10. Vérifier le bundle : `python scripts/verify_model_bundle.py`.
11. Tester les trois ECG externes : `python scripts/smoke_test_real_inference.py`.
12. Lancer : `python run.py`.
13. Ouvrir `http://127.0.0.1:5000`.

## 3. Recette fonctionnelle locale

Tester successivement :

- connexion administrateur ;
- page **Modèle & validation** ;
- exemple PTBDB contrôle sain ;
- exemple PTBDB MI ;
- exemple PTBDB proche du seuil ;
- historique ;
- PDF ;
- back-office ;
- explicabilité optionnelle.

Suivre la checklist `docs/RECETTE_V1.md` et conserver les captures.

## 4. Docker local avec PostgreSQL

1. Installer Docker Desktop.
2. Copier `.env.example` en `.env` et remplacer les secrets.
3. Exécuter `docker compose up --build`.
4. Ouvrir `http://localhost:5000`.
5. Vérifier `http://localhost:5000/api/v1/health`.
6. Arrêter avec `docker compose down`.

Le conteneur utilise un seul worker Gunicorn afin d'éviter de charger cinq modèles TensorFlow dans plusieurs processus.

## 5. GitHub

```bash
git init
git add .
git commit -m "CardioAI Assist V1"
git branch -M main
git remote add origin URL_DU_DEPOT
git push -u origin main
```

Ne jamais ajouter `.env`, mots de passe, clés API ni données nominatives.

## 6. Déploiement public

Le projet fournit `Dockerfile` et `render.yaml`. Avant de lancer un hébergement public, mesurer la mémoire réelle du conteneur avec les cinq modèles chargés. TensorFlow représente la principale consommation mémoire ; si le service manque de mémoire, il faut augmenter le plan plutôt que désactiver ou remplacer silencieusement le modèle.

Variables principales :

- `SECRET_KEY`
- `DATABASE_URL`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `API_KEY`
- `DEMO_MODE=false`
- `MODEL_DIR=/app/models`
- `MODEL_THRESHOLD=0.72`
- `MODEL_VERSION=raw-inceptiontime-se-nested-v1`
- `SESSION_COOKIE_SECURE=true` en HTTPS

## 7. Vérifications avant soutenance

1. `/api/v1/health` -> `status: ok` et `REAL_RAW_ENSEMBLE`.
2. Bundle `real_bundle_ready=true`.
3. Connexion jury.
4. Trois exemples PTBDB analysables.
5. Aucun `DEMO_SYNTHETIC` dans la démonstration finale.
6. PDF et historique fonctionnels.
7. Back-office administrateur fonctionnel.
8. Test Chrome, Edge et Firefox.
9. Dump PostgreSQL exporté après la recette.
10. URL publique, Git et identifiants de test ajoutés au ZIP final.

## 8. Dépannage

- `TensorFlow n'est pas installé` : réinstaller `requirements.txt` dans Python 3.11.
- `bundle invalide` : exécuter `python scripts/verify_model_bundle.py` et ne pas contourner l'erreur.
- erreur CSV : vérifier les noms exacts des 12 dérivations.
- signal trop court : le pipeline exige au moins 10 s après rééchantillonnage.
- erreur mémoire : conserver un worker, mesurer la RAM, augmenter les ressources ; désactiver temporairement XAI uniquement si nécessaire pour la latence.
- base indisponible : vérifier `DATABASE_URL` et PostgreSQL.
