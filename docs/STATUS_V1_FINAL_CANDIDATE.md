# Statut de la V1 Final Candidate

## Validé dans cette version

- Bundle réel 15/15 avec SHA-256.
- 5 modèles RAW InceptionTime-SE, 502 497 paramètres chacun.
- 5 scalers fold-wise.
- Reproduction des OOF PTB-XL réalisée dans l'étape 2.
- Pipeline exact de l'application validé sur PTBDB dans l'étape 2B.
- Exemples publics de démonstration remplacés par des ECG PTBDB externes.
- Suppression du fallback silencieux vers la prédiction synthétique.
- Rejet des signaux <10 s pour rester cohérent avec le pipeline validé.
- CSV strict sur les noms des dérivations pour éviter une erreur silencieuse d'ordre.
- Back-office administrateur ajouté.
- Page de validation et limites ajoutée.
- Traçabilité du bundle et qualité technique ajoutées aux résultats.
- PDF enrichi.
- Code Python compilé statiquement sans erreur.
- Script de contrôle du bundle exécuté avec succès dans l'environnement de génération.

## À exécuter sur une machine avec les dépendances complètes

- installation de Flask/TensorFlow ;
- `pytest -q` ;
- `python scripts/smoke_test_real_inference.py` ;
- recette web complète ;
- mesure RAM et latence ;
- Docker/PostgreSQL ;
- déploiement HTTPS ;
- tests multi-navigateurs ;
- export du dump PostgreSQL réel.

Ces opérations doivent produire les preuves finales du mémoire. Aucune d'elles ne doit être déclarée réussie avant exécution réelle.
