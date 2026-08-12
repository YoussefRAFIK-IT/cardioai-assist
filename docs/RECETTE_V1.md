# Recette V1 — à exécuter avant déploiement public

## Bundle
- [ ] `python scripts/verify_model_bundle.py` -> BUNDLE VALIDE
- [ ] `python scripts/smoke_test_real_inference.py` -> 3 prédictions REAL_RAW_ENSEMBLE

## Fonctionnel
- [ ] Connexion administrateur
- [ ] Création d'un utilisateur analyste
- [ ] Analyse de `ptbdb_demo_healthy_correct.csv`
- [ ] Analyse de `ptbdb_demo_mi_correct.csv`
- [ ] Analyse de `ptbdb_demo_borderline_correct.csv`
- [ ] Résultat stocké dans l'historique
- [ ] PDF généré
- [ ] XAI optionnelle affichée
- [ ] Page Modèle & validation accessible
- [ ] Back-office admin accessible uniquement à l'admin

## Erreurs attendues
- [ ] CSV sans noms de dérivations -> rejet
- [ ] signal < 10 s -> rejet
- [ ] dérivation manquante -> rejet
- [ ] >10 % NaN -> rejet
- [ ] bundle altéré en mode réel -> erreur bloquante, jamais DEMO_SYNTHETIC

## Sécurité / accès
- [ ] SECRET_KEY remplacée
- [ ] ADMIN_PASSWORD remplacé
- [ ] API_KEY remplacée
- [ ] SESSION_COOKIE_SECURE=true en HTTPS
- [ ] test Chrome
- [ ] test Edge
- [ ] test Firefox

## Preuves à capturer
- [ ] `/api/v1/health`
- [ ] dashboard réel
- [ ] résultat MI
- [ ] résultat NORM
- [ ] cas proche seuil
- [ ] historique
- [ ] PDF
- [ ] administration
- [ ] PostgreSQL
- [ ] logs Render/Docker
