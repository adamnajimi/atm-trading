# Matrice de compétences des agents (preuve = test ou résultat observable)

| Agent (module) | Compétence | Preuve | Niveau |
| --- | --- | --- | --- |
| Données (`data/`) | Télécharger, valider, détecter trous et sauts | `test_data_and_strategy.py`, run research | Acquis |
| Stratégies (`strategies/`) | Décider sans regarder l'avenir | `test_lookahead.py` | Acquis |
| Risque (`risk.py`) | Refuser tout dépassement de limite, arrondi prudent | `test_risk.py`, `test_config.py` | Acquis |
| Exécution (`execution/`) | Ordres idempotents, stop en paper | `test_execution.py`, `test_paper_shadow.py` | Acquis |
| Backtest (`backtest/`) | Exécution à t+1, frais, benchmarks | `test_integration.py` | Acquis |
| Statistiques (`metrics.py`) | Pénaliser le nombre d'essais (DSR) | `test_research.py` | Nouveau |
| Recherche (`research.py`) | Scénarios coûts/capital sans toucher au test final | `test_research.py` | Acquis |
| Exécution limite | Simuler un ordre limite et son remplissage | aucune | Manquant |
| Information (X, actualités) | Vérifier une source | aucune | Manquant |
| Observabilité | Journal d'événements structuré, Command Center, Virtual Office | `test_events.py`, `test_paper_shadow.py` | Acquis |
| Rejeu | Décision à une date passée sans information future | `test_lookahead.py::test_replay_uses_only_past_bars` | Acquis |
