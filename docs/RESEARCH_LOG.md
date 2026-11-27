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

## Rejetées

| Nom | Date | Raison |
| --- | --- | --- |
| trend_sma sur ETH/EUR | 2026-11-27 | Rendement net −0,9 % en validation, sous le cash |
| rsi_dip (BTC) | 2026-11-27 | Backtest : −1,1 % en entraînement, −0,4 % en validation, seulement 6 allers-retours au total ; n'entre pas en fantôme |

## Mise en garde

Les paramètres de trend_sma_fast ont été choisis après avoir vu la grille de sensibilité d'entraînement (SMA 50 et stop 2×ATR y étaient parmi les meilleurs). Son backtest est donc optimiste par construction : seule l'évaluation fantôme sur données nouvelles compte.
