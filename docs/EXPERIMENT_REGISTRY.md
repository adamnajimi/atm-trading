# Registre des expériences

Chaque expérience est notée **avant** son lancement (hypothèse, critère d'arrêt), résultats négatifs compris.

| ID | Date | Hypothèse | Protocole et critère | Résultat | Statut |
| --- | --- | --- | --- | --- | --- |
| E1 | 2026-11-27 | trend_sma bat le cash après frais | Entraînement + validation, test final unique | +3,9 % au test final, avantage faible | Terminé : paper trading |
| E2 | 2026-11-27 | rsi_dip bat le cash | Entraînement + validation | Sous le cash | Rejeté |
| E3 | 2026-11-27 | Limites d'essai (0,5–2 €/trade) | Marge ≥ 3 € avant l'arrêt à 7 € | 1,5 €/trade gardé pour trend_sma seulement | Fantôme |
| E4 | 2026-11-28 | Des frais plus bas (Bitvavo, ordres limites) améliorent le résultat | 4 scénarios de coûts, BTC | Validation +16,7 % → +28,5 % (Bitvavo taker) | Proposé à Adam |
| E5 | 2026-11-28 | 50 € de capital améliore le résultat | Mêmes limites vs limites relevées | Aucun gain à limites égales | Proposé à Adam |
| E6 | 2026-11-28 | Le moteur et les stratégies ne regardent pas l'avenir | Décisions identiques avec et sans barres futures (3 coupures) | Passe pour les 3 stratégies | Test permanent |
| E7 | 2026-11-28 | L'avantage de validation survit au nombre d'essais | Sharpe déflaté sur tous les essais BTC de validation ; seuil 95 % | 45 essais ; trend_sma DSR 21,7 % ; meilleur essai (Sharpe annualisé 1,17) DSR 61,3 % (run 46121423431) | Terminé : aucun avantage prouvé |
