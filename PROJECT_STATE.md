# PROJECT_STATE — ATM

Dernière mise à jour : 2026-11-27.

## Étape en cours

**A (recherche) terminée, B (développement) commencée.** Tout est en simulation. Aucun compte, aucune clé, aucun ordre réel.

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
- Tests : 36 tests unitaires et d'intégration passent (exécutés le 2026-11-27, Python 3.13, données synthétiques).
- Non testé : `atm/data/fetch.py` (le proxy du conteneur cloud bloque api.kraken.com) et le workflow GitHub (aucun dépôt encore).

## Tâches restantes

1. Adam crée un dépôt GitHub (public recommandé) et le donne au projet.
2. Télécharger l'historique réel BTC/EUR et ETH/EUR (GitHub Actions ou Mac).
3. Étape C : découpage train / validation / test final, walk-forward, figer les règles avant le test final.
4. Ajouter des stratégies candidates (retour à la moyenne, cash) et le benchmark DCA.
5. Étape D : critères de rejet, sensibilité, contribution marginale de chaque agent.
6. Tableau de bord HTML statique généré depuis `state/`.
7. Étape F : tests de panne supplémentaires (API indisponible, données manipulées).
8. Vérifier avant l'étape G : frais SEPA Kraken, minimum Coinbase, liste blanche AMF, BOFiP (305 €, 31,4 %).

## Résultats obtenus

Aucun résultat de performance réel. Les backtests synthétiques servent uniquement à tester le moteur.
