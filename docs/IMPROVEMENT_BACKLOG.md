# Backlog d'améliorations et prochaines actions

Remplace aussi NEXT_ACTIONS et LEARNING_ROADMAP. Correspondances : FAILURE_DATABASE = `LESSONS.md`, STRATEGY_REGISTRY = `RESEARCH_LOG.md`.

## En attente d'Adam
1. Coûts Bitvavo pour le paper trading (changement de paramètre).
2. Portefeuille fictif de 50 € (limites intermédiaires ou proportionnelles).

## Prochaines actions (simulation)
1. Fait le 2026-11-28 : journal d'événements (`state/events.jsonl`) et Command Center statique (`docs/dashboard/`). Reste : publication GitHub Pages (réglage à activer par Adam), événements de la recherche, mode « Virtual Office ».
3. Protection après série de stops (idée Freqtrade StoplossGuard) : backtest, puis fantôme.
4. Probabilité de surapprentissage (CSCV) sur les grilles de paramètres.
5. Accès X : étudier l'API officielle (coût, conditions) ; proposition budgétaire seulement si utile.
6. Sources gratuites : flux RSS officiels (BCE, Fed, AMF), calendrier économique.
7. Rejeu d'une date passée sans information future (le test anti-lookahead en est la base).

## Compétences à acquérir (mesurées par des tests)
- Détection de surapprentissage : DSR fait ; CSCV à faire.
- Modèle d'exécution par ordres limites (taux de remplissage réaliste).
- Event study sans lookahead.
