# Cahier de tests V1

| ID | Scénario | Résultat attendu |
|---|---|---|
| AUTH-01 | Connexion valide | Accès dashboard |
| AUTH-02 | Mot de passe invalide | Refus générique |
| ADMIN-01 | Analyste ouvre /admin | HTTP 403 |
| ADMIN-02 | Admin crée analyste | Utilisateur créé et audité |
| ECG-01 | CSV 1000×12 nommé, 100 Hz | 1 segment |
| ECG-02 | ECG long | 5 segments positions validées |
| ECG-03 | 1000 Hz | conversion 100 Hz |
| ECG-04 | dérivation manquante | rejet explicite |
| ECG-05 | >10 % NaN | rejet explicite |
| ECG-06 | durée <10 s | rejet explicite, aucun zero-padding |
| ECG-07 | CSV sans noms de leads | rejet pour éviter erreur d'ordre |
| AI-01 | Real bundle valide | REAL_RAW_ENSEMBLE |
| AI-02 | Bundle altéré + DEMO_MODE=false | erreur bloquante, aucun fallback |
| AI-03 | DEMO_MODE=true | DEMO_SYNTHETIC explicitement visible |
| AI-04 | exemple PTBDB healthy | prédiction réelle |
| AI-05 | exemple PTBDB MI | prédiction réelle |
| XAI-01 | Occlusion activée | lead + temps |
| API-01 | /health réel valide | 200 / status ok |
| API-02 | /health bundle invalide | 503 / degraded |
| SEC-01 | fichier >8 Mo | HTTP 413 |
| SEC-02 | API sans clé | 401/503 |
| DB-01 | prédiction | ECG + prediction + audit |
| REP-01 | PDF | téléchargement OK |
| A11Y-01 | clavier | focus visible, ordre logique |
