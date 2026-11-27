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
| trend_sma_fast | Même hypothèse, SMA 50 / momentum 30, stop 2×ATR (assez serré pour respecter le minimum de 5 €) | 2026-11-28 | En évaluation |
| rsi_dip | Repli court (RSI14 < 30) dans une tendance longue (clôture > SMA200), sortie RSI > 55 ou 10 jours | 2026-11-28 | En évaluation |

## Rejetées

| Nom | Date | Raison |
| --- | --- | --- |
| trend_sma sur ETH/EUR | 2026-11-27 | Rendement net −0,9 % en validation, sous le cash |
