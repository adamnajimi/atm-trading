# ATM — trading algorithmique en simulation

Système de trading crypto spot, entièrement déterministe, **en simulation par défaut**.
Le trading réel est bloqué dans le code (`atm/execution/live.py`) jusqu'à l'étape G.

## Installation (Mac)

```bash
cd atm
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

## Commandes

```bash
python -m atm.cli backtest --synthetic          # test du moteur sur données factices
python -m atm.cli backtest --data btc_eur.csv   # backtest sur un CSV OHLCV journalier
python -m atm.cli paper                          # un cycle de paper trading (télécharge les prix publics)
python -m atm.cli status                         # état du portefeuille simulé
```

Télécharger l'historique BTC/EUR (prix publics Kraken, sans compte) :

```bash
python -c "from atm.data.fetch import *; save_csv(fetch_daily_ohlcv('BTC/EUR', since='2017-01-01T00:00:00Z'), 'btc_eur.csv')"
```

## Arrêt d'urgence

N'importe laquelle de ces actions arrête tout nouvel achat et déclenche la vente des positions au cycle suivant :

- créer un fichier `KILL_SWITCH` à la racine du dépôt ;
- définir la variable GitHub `ATM_KILL_SWITCH=1` (Settings > Secrets and variables > Actions > Variables) ;
- désactiver le workflow `paper-trading` dans l'onglet Actions.

## Architecture

| Module | Rôle (agents du cahier des charges) |
| --- | --- |
| `atm/data/` | Agent 2 : téléchargement, validation, horodatage |
| `atm/strategies/` | Agents 3, 4, 7, 8 : stratégies codifiées, figées |
| `atm/orchestrator.py` | Agent 0 : cycle de décision, vote pondéré |
| `atm/risk.py` | Agent 10 : veto absolu, limites, suspension |
| `atm/execution/` | Agent 13 : paper broker, broker réel désactivé |
| `atm/backtest/` | Agents 11 et 12 : backtest chronologique, statistiques |
| `atm/audit.py` | Agent 15 : journal horodaté, rapport quotidien |
| `atm/killswitch.py` | Agent 14 : arrêt d'urgence |

## Limites de risque (codées, refusées si relâchées)

- Perte maximale contractuelle : 10 € ; arrêt opérationnel à 7 € (frais et pertes latentes inclus).
- Perte maximale par trade : 1 € (stop × 1,5 pour les gaps + frais aller-retour) ; par jour : 2 €.
- Pas de levier, pas de vente à découvert, pas de martingale.

## Limites connues

- Le paper trading exécute au dernier cours de clôture connu, pas au prix réel du carnet d'ordres.
- GitHub Actions peut retarder ou abandonner une exécution planifiée : le système n'est pas 24 h/24.
- La stratégie `trend_sma` est une **candidate non validée** ; aucun résultat réel n'a encore été produit.
