# Recherche scientifique — notes vérifiées

| Travail | Idée | Applicable à ATM ? | Action |
| --- | --- | --- | --- |
| Bailey & López de Prado (2014), *The Deflated Sharpe Ratio* | Le meilleur Sharpe parmi N essais est gonflé par le hasard ; le DSR donne la probabilité qu'il soit réel, en tenant compte de N, de l'asymétrie et des queues épaisses | Oui : on a comparé des dizaines de variantes sur la même validation | Implémenté (`metrics.deflated_sharpe`), affiché par le workflow research |
| Bailey, Borwein, López de Prado & Zhu (2017), *The Probability of Backtest Overfitting* | Validation croisée combinatoire : fréquence à laquelle le meilleur en échantillon est sous la médiane hors échantillon | Oui, mais demande beaucoup de segments | Backlog |
| Lo (2004), *Adaptive Markets Hypothesis* | Les avantages apparaissent et disparaissent selon les régimes | Oui : justifie les fantômes sur données nouvelles et l'abandon rapide | Déjà dans les règles |
| Moskowitz, Ooi & Pedersen (2012), *Time Series Momentum* | Persistance des tendances sur 1–12 mois, plusieurs classes d'actifs | C'est l'hypothèse de trend_sma | Déjà testée ; avantage faible après frais |

Règle : une affirmation (article, post X, README) n'est retenue qu'après un backtest sur entraînement + validation puis un fantôme sur données postérieures au 2026-11-26.
