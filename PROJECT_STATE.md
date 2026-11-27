# PROJECT_STATE — ATM

Dernière mise à jour : 2026-11-27.

## Étape en cours

**A, B, C terminées ; D passée pour BTC seul (2026-11-27). E (paper trading BTC) démarrée le 2026-11-27 : PR #1 fusionnée, premier cycle manuel réussi (NO_TRADE), puis chaque jour à 01:17 UTC. Fin au plus tôt le 2027-01-26.** Tout est en simulation. Aucun compte, aucune clé, aucun ordre réel.

Rapport de faisabilité : https://claude.ai/artifact/7Fqjaz64b8QCfKD2RhSCkc

## Contraintes d'Adam (non négociables)

- Capital 20 €, perte totale max 10 € (réalisée + latente + frais). Budget logiciel 0 €. Claude Pro uniquement.
- Objectif 500 € au 15/12/2026 = ambition, jamais une raison de trader.
- Réel, levier, comptes, identifiants : uniquement avec l'accord explicite d'Adam.
- Retraits désactivés, kill switch obligatoire, simulation par défaut.

## Décisions prises (2026-11-27)

| Décision | Justification |
| --- | --- |
| Objectif 500 € au 15/12/2026 jugé irréalisable | 18 jours restants ; +19,9 %/jour requis ; étapes C–F non raccourcissables |
| Architecture B : Python déterministe + GitHub Actions (dépôt public) + Claude en supervision | Seule option à 0 € reproductible et sans Mac allumé |
| Claude ne décide aucun trade | API payante ; LLM non reproductible et biaisé en backtest (connaît l'histoire) |
| Marché : crypto spot BTC/EUR, ETH/EUR | Minimum 5 € chez Kraken ; actions exclues (IBKR 1,25 €/ordre min) |
| Plateforme d'exécution visée : Kraken (Payward Europe, passeport MiCA) ; Coinbase en alternative | Binance France radiée, fermeture des comptes 31/12/2026 |
| Fréquence : journalière | Frais aller-retour 0,8–1,6 % |
| Arrêt opérationnel à 7 €, 1 €/trade, 2 €/jour, pas de levier | Marge de 3 € pour gaps, slippage, pannes |
| Agents 5 (macro) et 6 (sentiment) reportés | Sources fiables payantes ou nécessitant un LLM |
| Paper trading : 60 jours minimum, 20 décisions minimum | Critère fixé avant de commencer |

## Code (dossier `atm/`)

- Fait : config validée (refuse toute limite relâchée), modèles de messages, gestionnaire de risques, kill switch, validation des données, stratégie candidate `trend_sma`, orchestrateur + vote pondéré, moteur de backtest chronologique, statistiques, paper broker idempotent, broker réel bloqué, journal d'audit, rapport quotidien, CLI, workflow GitHub Actions.
- Dépôt : https://github.com/adamnajimi/atm-trading, PR #1 fusionnée dans main le 2026-11-27. Branche en cours : `claude/autonomous-research`.
- Tests : 43 tests passent (conteneur Python 3.13 et GitHub Actions Python 3.12, 2026-11-27).
- Workflow `research` (push sur claude/** ou main) : télécharge les prix publics Coinbase Exchange, contrôle Kraken, lance la recherche. Workflow `paper` désactivé jusqu'à l'étape D.
- Le conteneur cloud ne peut pas télécharger les artefacts GitHub (stockage blob bloqué) : lire les résultats dans les logs du job.

## Progression autonome (demandée par Adam le 2026-11-27)

- Journal des erreurs et leçons : `docs/LESSONS.md`. Journal de recherche et critères de promotion figés : `docs/RESEARCH_LOG.md`.
- Candidates `trend_sma_fast` et `rsi_dip` évaluées en portefeuilles fantômes (20 € fictifs chacun, `state/shadow/`) à partir du 2026-11-28, sans effet sur le principal.
- Revue hebdomadaire par Claude (tâche planifiée) : lit les rapports, met à jour les journaux, propose de nouvelles candidates. Ne touche jamais aux limites de risque.

## Tâches restantes

1. Suivre le paper trading (rapports dans state/reports/ sur main).
2. Étape E : 60 jours et 20 décisions minimum ; comparer le suivi au backtest.
3. Toute nouvelle stratégie : évaluée uniquement sur des données postérieures au 2026-11-26.
6. Tableau de bord HTML statique généré depuis `state/`.
7. Étape F : tests de panne supplémentaires (API indisponible, données manipulées).
8. Vérifier avant l'étape G : frais SEPA Kraken, minimum Coinbase, liste blanche AMF, BOFiP (305 €, 31,4 %).

## Résultats obtenus

Run GitHub Actions 46059699517 (2026-11-27), données Coinbase Exchange BTC/EUR 2015-04-23→2026-11-26 (4236 barres), ETH/EUR 2017-05-23→2026-11-26 (3473 barres). trend_sma, paramètres fixés avant les données (SMA 100, momentum 50, stop 3×ATR), capital 20 €, frais Kraken taker 0,8 % + 0,1 % slippage. Test final (≥ 2024-07-01) non exécuté.

| Actif | Segment | Net | Max DD | Perte max | Allers-retours | Frais | Buy & hold | DD B&H |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTC | entraînement 2015–2021 | +277,7 % | −20,9 % | 1,09 € | 28 | 3,82 € | +13 210 % | −83,1 % |
| BTC | validation 2022–mi-2024 | +16,7 % | −15,3 % | 2,57 € | 19 | 2,02 € | +41,0 % | −64,1 % |
| ETH | entraînement 2017–2021 | +122,3 % | −32,0 % | 0,81 € | 9 | 0,97 € | +1 998 % | −93,5 % |
| ETH | validation 2022–mi-2024 | −0,9 % | −18,7 % | 2,82 € | 15 | 1,60 € | −2,9 % | −71,9 % |

Lecture : perte max toujours < 7 € ; ETH ne bat pas le cash en validation (rejet ETH selon le critère D) ; BTC bat le cash mais pas le buy & hold ; les frais = 10 % du capital sur la validation BTC. Sensibilité (entraînement) : les 12 combinaisons BTC sont positives ; ETH très sensible au stop. 

### Vérification des données (run 46069483279)

Les variations > 50 % signalées sont le krach réel du 12/03/2020 (BTC −37,4 %, ETH −41,9 % le même jour). Trous : BTC 2016-07-12, ETH 2017-05-27/28. Rien d'anormal dans la période de test final. Coinbase a renvoyé 4235 barres BTC au lieu de 4236 une heure plus tôt : une barre de 2016 a disparu, à surveiller.

Achat régulier (4×5 €) en validation : BTC +94,8 %, ETH +56,7 %, nettement mieux que trend_sma (+16,7 %, −0,9 %).

### Test final unique (run 46069677731) — RÉUSSI, de justesse

BTC/EUR 2024-07-01 → 2026-11-26 (879 jours) : +3,9 % (20,78 €), DD −18,5 %, perte max 0,76 €, 21 allers-retours, frais 2,37 €, 19 % de trades gagnants. Buy & hold −7,3 % (DD −51,7 %), achat régulier −27,0 %. Les trois critères figés sont remplis. Avantage faible : +0,78 € en 2,4 ans, moins que les frais payés ; 21 trades ne suffisent pas à le distinguer du hasard. Marqueur `results/FINAL_TEST_DONE.json` : le test ne peut plus être relancé.

### Essai à blanc du paper trading (run du 2026-11-27)

Cycle complet sur prix Kraken réels : NO_TRADE (BTC 55 164 € sous sa SMA100 68 439 €). Avec la volatilité actuelle, le stop vaut 17 % : la taille autorisée (≈3,7 €) est sous le minimum de 5 €, donc aucun achat n'est possible même en tendance haussière tant que la volatilité reste à ce niveau.
