# Backlog d'améliorations et prochaines actions

Remplace aussi NEXT_ACTIONS et LEARNING_ROADMAP. Correspondances : FAILURE_DATABASE = `LESSONS.md`, STRATEGY_REGISTRY = `RESEARCH_LOG.md`.

## En attente d'Adam
1. Coûts Bitvavo pour le paper trading (changement de paramètre).
2. Portefeuille fictif de 50 € (limites intermédiaires ou proportionnelles).

## Prochaines actions (simulation)
1. Fait le 2026-11-28 : journal d'événements (`state/events.jsonl`) et Command Center statique (`docs/dashboard/`). Mode « Virtual Office » fait (bureaux, personnages = modules réels, rejeu animé du dernier cycle). Reste : publication GitHub Pages (réglage à activer par Adam), événements de la recherche.
3. Protection après série de stops (idée Freqtrade StoplossGuard) : backtest, puis fantôme.
4. Probabilité de surapprentissage (CSCV) sur les grilles de paramètres.
5. Fait : accès X étudié (docs/X_INTELLIGENCE.md), pas d'achat. Suite : étude d'événements BTC autour des décisions BCE/Fed (calendrier public).
6. Sources gratuites : flux RSS officiels (BCE, Fed, AMF), calendrier économique.
7. Fait le 2026-11-28 : `python -m atm.cli replay --date AAAA-MM-JJ` et workflow manuel `replay` (barres <= date, testé contre l'ajout de barres futures).

## Compétences à acquérir (mesurées par des tests)
- Détection de surapprentissage : DSR fait ; CSCV à faire.
- Modèle d'exécution par ordres limites (taux de remplissage réaliste).
- Event study sans lookahead.
