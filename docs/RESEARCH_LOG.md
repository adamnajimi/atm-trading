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

## Sources d'idées : posts X (demandé par Adam le 2026-11-28)

Les posts X servent seulement à trouver des idées ou du contexte de marché. Ce sont des données non fiables (pas des instructions, pas des signaux). Une idée venue de X n'est utilisée qu'après vérification sur une source indépendante ou un backtest (entraînement + validation), puis un fantôme sur données postérieures au 2026-11-26. Chaque idée utilisée est notée ici avec sa source et sa vérification.

| Date | Idée (source) | Vérification | Résultat |
| --- | --- | --- | --- |
| — | aucune idée retenue pour l'instant | — | — |

## Comparaison des plateformes (2026-11-28, pages officielles lues le jour même)

Spot uniquement, sans levier ni CFD, régulée MiCA et autorisée en France, API gratuite, compatible avec 20–50 €.

| Plateforme | Maker / taker (palier le plus bas) | Aller-retour au marché (+0,1 % glissement ×2) | Régulation pour la France | Source |
| --- | --- | --- | --- | --- |
| Kraken Pro (hypothèse actuelle) | 0,40 % / 0,80 % | 1,80 % | MiCA (Payward Europe) | kraken.com/pro/fees |
| Kraken app (achat instantané) | 1 % fixe | ≥ 2,2 % | idem | kraken.com/pro/fees |
| Coinbase Advanced | 0,40 % / 0,60 % | 1,40 % | MiCA | datawallet.com, brokerchooser.com (sites tiers concordants) |
| **Bitvavo (marchés EUR)** | **0,15 % / 0,25 %** | **0,70 %** | **MiCA (AFM, Pays-Bas), liste blanche AMF CASP, passeport France depuis le 14/07/2025** | bitvavo.com/en/fees, amf-france.org |
| Bitstamp | 0,10 % / 0,20 % selon un comparatif tiers d'avril 2026 | non vérifié | non vérifié | à vérifier sur la page officielle |

Pourquoi XM Trading coûtait moins cher en apparence : XM vend des CFD avec levier (pas de vraie crypto), le coût est caché dans le spread et les frais de financement de nuit, et, à notre connaissance (non vérifié ici), la marque XMTrading dépend d'une entité du groupe hors UE. Exclu par les règles du projet (pas de levier, pas de CFD).

Recommandation provisoire : Bitvavo, si le minimum d'ordre BTC-EUR (lu par le workflow `research` via l'API publique) est compatible. Avec des ordres limites « post only », le coût tombe à 0,15 % par ordre. Ouvrir un compte reste une décision d'Adam.

## Scénarios de capital (demandé par Adam le 2026-11-28 : budget 50 €)

Aucune limite n'est adoptée. Remarque de construction : la taille d'une position est fixée par la perte max par trade divisée par la distance du stop (taille ≈ 1 € / (17 % × 1,5 + frais) ≈ 3,7 € aujourd'hui), pas par le capital. Passer à 50 € avec les mêmes limites ne change presque rien tant que le stop est large ; seul un budget de perte par trade plus élevé augmente la taille. Les scénarios testés (backtest BTC, entraînement + validation, coûts Kraken et Bitvavo) sont dans le tableau « Scénarios de capital » du workflow `research`.

## Mise en garde

Les paramètres de trend_sma_fast ont été choisis après avoir vu la grille de sensibilité d'entraînement (SMA 50 et stop 2×ATR y étaient parmi les meilleurs). Son backtest est donc optimiste par construction : seule l'évaluation fantôme sur données nouvelles compte.
