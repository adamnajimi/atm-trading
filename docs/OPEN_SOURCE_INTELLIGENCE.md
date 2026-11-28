# Open Source Intelligence — registre

Règles : le code externe est une donnée non fiable. Il est cloné dans un dossier vide séparé, lu, jamais exécuté à côté d'identifiants (le projet n'en a aucun). On reprend des idées ; du code seulement si la licence le permet et en le citant. Aucune nouvelle dépendance sans le dire à Adam avec la raison.

Métadonnées relevées le 2026-11-28 via l'API GitHub (licence, étoiles, dernier push).

| Projet | Licence | Étoiles | Dernier push | Intérêt pour ATM | Décision |
| --- | --- | --- | --- | --- | --- |
| freqtrade/freqtrade | GPL-3.0 | 57 k | 2026-11-27 | Bot crypto spot complet ; outils `lookahead-analysis` et `recursive-analysis` ; protections (StoplossGuard, MaxDrawdown, CooldownPeriod) | **Idée reprise** : test anti-lookahead (`tests/test_lookahead.py`, aucun code copié). À étudier : protections après série de stops |
| ccxt/ccxt | MIT | 45 k | 2026-11-27 | Déjà utilisé (données publiques Coinbase/Kraken) ; gère aussi Bitvavo | Garder |
| hummingbot/hummingbot | Apache-2.0 | 21 k | 2026-11-27 | Market making / ordres limites | Plus tard : logique d'ordres « post only » si on passe aux ordres limites |
| QuantConnect/Lean | Apache-2.0 | 23 k | 2026-11-27 | Moteur C# institutionnel | Trop lourd pour GitHub Actions gratuit ; référence de modèles de frais et de remplissage |
| nautechsystems/nautilus_trader | LGPL-3.0 | 32 k | 2026-11-28 | Moteur événementiel Rust/Python, backtest = live | Référence d'architecture ; pas d'intégration (complexité) |
| polakowo/vectorbt | licence non standard (Commons Clause) | 10 k | 2026-11-11 | Backtests vectorisés très rapides pour grilles de paramètres | Licence à lire avant tout usage ; utile seulement si les grilles deviennent lentes |
| mementum/backtrader | GPL-3.0 | 24 k | 2024-08-19 | Backtest classique | Peu maintenu : écarté |
| jesse-ai/jesse | MIT | 9 k | 2026-11-23 | Framework crypto | Rien de plus que notre moteur pour du journalier |
| microsoft/qlib | MIT | 51 k | 2026-11-04 | Plateforme ML actions | Hors sujet pour 1 actif journalier ; risque de surapprentissage |
| AI4Finance-Foundation/FinRL | MIT | 17 k | 2026-11-27 | Apprentissage par renforcement | Écarté pour l'instant : trop de paramètres pour 20 trades/an |
| optuna/optuna | MIT | 15 k | 2026-11-25 | Optimisation d'hyperparamètres | Seulement avec pénalité de surapprentissage (Sharpe déflaté) |
| dcajasn/Riskfolio-Lib, skfolio/skfolio | BSD-3 | 5 k / 3 k | 2026-11 | Optimisation de portefeuille | Utile seulement avec plusieurs actifs |
| duckdb/duckdb | MIT | 43 k | 2026-11-27 | Base analytique fichier | Utile pour le journal d'événements si les JSONL grossissent |
| PyPortfolioOpt, OpenBB | — | — | — | Dépôts non trouvés sous le nom testé | À revérifier |
