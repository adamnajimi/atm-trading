# Backlog d'améliorations et prochaines actions

Remplace aussi NEXT_ACTIONS et LEARNING_ROADMAP. Correspondances : FAILURE_DATABASE = `LESSONS.md`, STRATEGY_REGISTRY = `RESEARCH_LOG.md`.

## En attente d'Adam
1. Coûts Bitvavo pour le paper trading (changement de paramètre).
2. Portefeuille fictif de 50 € (limites intermédiaires ou proportionnelles).

## Prochaines actions (simulation)
1. Journal d'événements structuré (id, horodatage, agent, type, tâche, statut, résultat, durée, sources, erreurs) écrit par chaque cycle et chaque recherche.
2. Tableau de bord statique (GitHub Pages) lu depuis `state/` et le journal : mode « Command Center » d'abord, « Virtual Office » ensuite, uniquement à partir d'événements réels.
3. Protection après série de stops (idée Freqtrade StoplossGuard) : backtest, puis fantôme.
4. Probabilité de surapprentissage (CSCV) sur les grilles de paramètres.
5. Accès X : étudier l'API officielle (coût, conditions) ; proposition budgétaire seulement si utile.
6. Sources gratuites : flux RSS officiels (BCE, Fed, AMF), calendrier économique.
7. Rejeu d'une date passée sans information future (le test anti-lookahead en est la base).

## Compétences à acquérir (mesurées par des tests)
- Détection de surapprentissage : DSR fait ; CSCV à faire.
- Modèle d'exécution par ordres limites (taux de remplissage réaliste).
- Event study sans lookahead.
