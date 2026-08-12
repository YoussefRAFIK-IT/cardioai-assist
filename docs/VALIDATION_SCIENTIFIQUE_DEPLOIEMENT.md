# Validation scientifique du pipeline de déploiement

## 1. Reproductibilité interne
Les cinq artefacts Keras et leurs scalers reproduisent les probabilités OOF PTB-XL à une différence numérique négligeable. Les métriques RAW OOF sont donc reproductibles à partir du bundle sauvegardé.

## 2. Pipeline réellement déployé
L'application n'utilise pas la Late Fusion. Elle applique les cinq modèles RAW à chaque fenêtre, chacun avec son scaler fold-wise, moyenne les cinq probabilités puis moyenne les fenêtres pour les ECG longs.

## 3. Validation externe PTBDB
La validation exacte du pipeline a utilisé 448 enregistrements, 200 patients et 2240 fenêtres. Au niveau patient, ROC-AUC=0,9461 et PR-AUC=0,9824. Au seuil interne verrouillé 0,72, sensibilité=0,5405 et spécificité observée=1,0.

## 4. Interprétation
La capacité de classement se transporte mieux que la calibration et le seuil. Le prototype expose donc la probabilité, le seuil, la version du modèle et un avertissement. Il n'est pas présenté comme dispositif médical.

## 5. Seuils alternatifs
Les seuils 0,43 (F1) et 0,60 (balanced accuracy) ont été identifiés après observation de PTBDB. Ils sont post-hoc, exploratoires et ne sont pas activés par défaut.
