# Journal de recherche

## Règles permanentes

1. Le test final historique (2024-07-01 → 2026-11-26) est consommé. Toute nouvelle stratégie est jugée sur des données **postérieures au 2026-11-26**, en portefeuille fantôme.
2. Avant d'entrer en fantôme, une candidate est backtestée sur entraînement + validation (workflow `research`). Une candidate qui perd plus que le cash sur les deux segments n'entre pas.
3. Les critères de promotion sont fixés **avant** le début de l'évaluation et ne sont jamais modifiés après coup.
4. Promotion = remplacement de la stratégie du portefeuille fictif principal. Le passage à l'argent réel exige toujours l'accord explicite d'Adam.
5. Les limites de risque (7 €, 1 €/trade, 2 €/jour, pas de levier) ne changent jamais, pour aucune candidate.

## Critères de promotion (fixés le 2026-11-27)

Une candidate peut remplacer `trend_sma` si, sur son évaluation fantôme :

- au moins 60 jours et au moins 10 allers-retours ;
- valeur finale > 20 € (bat le cash) et > valeur du portefeuille principal sur la même période ;
- perte maximale < 7 €, aucune suspension ;
- frais totaux < gain brut.

Sinon elle est rejetée et notée ci-dessous avec la raison.

## Candidates

| Nom | Hypothèse | Entrée en fantôme | Statut |
| --- | --- | --- | --- |
| trend_sma (principal) | Persistance des tendances de plusieurs semaines | 2026-11-27 (portefeuille principal) | En paper trading |
| trend_sma_fast | Même hypothèse, SMA 50 / momentum 30, stop 2×ATR (assez serré pour respecter le minimum de 5 €). Backtest BTC : entraînement +472 % (55 allers-retours, 9,04 € de frais), validation +45,8 % (perte max 3,96 €) contre +16,7 % pour le principal | 2026-11-28 | En évaluation |
| trend_sma_risk15 | Même stratégie que le principal, perte max par trade 1,5 € au lieu de 1 € (essai autorisé par Adam, tests uniquement). Backtest BTC : entraînement +415,6 % (perte max 1,87 €), validation +26,1 % (perte max 3,57 €) contre +16,7 %. Avec la volatilité actuelle, la taille autorisée (~5,5 €) dépasse le minimum de 5 € | 2026-11-28 | En évaluation |

## Essais de limites de risque (2026-11-27)

Bornes d'essai codées (`config.TRIAL_BOUNDS`) : perte par trade 0,25–2 €, perte journalière 0,5–3 €, facteur gap ≥ 1,25. Arrêt à 7 € et perte totale de 10 € non modifiables. Six jeux testés sur trend_sma et trend_sma_fast (BTC). Retenu pour le fantôme : 1,5 €/trade sur trend_sma seulement. Rejetés : 2 €/trade (perte 4,77 € et 6,79 € en validation), 1,5 €/trade sur trend_sma_fast (5,85 €), 1,5 € + gap 1,25 (6,64 €), car trop près de l'arrêt à 7 €. Ces choix sont faits après avoir vu 12 combinaisons : biais de sélection, seul le fantôme comptera.

## Rejetées

| Nom | Date | Raison |
| --- | --- | --- |
| trend_sma sur ETH/EUR | 2026-11-27 | Rendement net −0,9 % en validation, sous le cash |
| Limite 2 €/trade | 2026-11-27 | Perte max en validation 4,77 € (trend_sma) et 6,79 € (trend_sma_fast) : marge insuffisante avant 7 € |
| rsi_dip (BTC) | 2026-11-27 | Backtest : −1,1 % en entraînement, −0,4 % en validation, seulement 6 allers-retours au total ; n'entre pas en fantôme |

## Mise en garde

Les paramètres de trend_sma_fast ont été choisis après avoir vu la grille de sensibilité d'entraînement (SMA 50 et stop 2×ATR y étaient parmi les meilleurs). Son backtest est donc optimiste par construction : seule l'évaluation fantôme sur données nouvelles compte.
