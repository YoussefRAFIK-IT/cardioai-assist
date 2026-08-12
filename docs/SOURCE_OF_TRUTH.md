# Source of Truth — CardioAI Assist V1

## Pipeline applicatif officiel

- Tâche : MI versus strict NORM.
- Entrée : ECG 12 dérivations, 100 Hz, fenêtres de 10 secondes (1000 × 12).
- Modèle : RAW InceptionTime-SE, ensemble de 5 modèles issus des 5 folds.
- Paramètres par modèle : 502 497.
- Normalisation : moyenne/écart-type propres à chaque fold.
- ECG long : cinq fenêtres (début, 25 %, centre, 75 %, fin).
- Agrégation : moyenne des cinq modèles par fenêtre, puis moyenne des fenêtres.
- Seuil de développement verrouillé : 0,72.

## Résultats internes PTB-XL officiels — OOF patient-wise

ROC-AUC 0,9777939 ; PR-AUC 0,9669649 ; Accuracy 0,9262622 ; Sensibilité 0,8879137 ; Spécificité 0,9493880 ; F1 0,9005935 ; Brier 0,059406.

Ces métriques décrivent les prédictions OOF, pas la moyenne simultanée des 5 modèles sur PTB-XL.

## Résultats externes officiels du pipeline exact de l'application — PTBDB, niveau patient

N=200 ; ROC-AUC 0,9460759 ; PR-AUC 0,9823804 ; Accuracy au seuil 0,72 = 0,66 ; Sensibilité 0,5405405 ; Spécificité observée 1,0 ; F1 0,7017544 ; Brier 0,1133043 ; ECE10 0,1366230.

Matrice au seuil 0,72 : TN=52, FP=0, FN=68, TP=80.

La conclusion à retenir est une forte discrimination externe associée à une mauvaise transportabilité du seuil/calibration. Les seuils 0,43 et 0,60 identifiés sur PTBDB restent exploratoires et ne remplacent pas le seuil verrouillé dans l'application.
