# Décisions d'architecture

| Date | Décision | Raison | Alternative écartée |
| --- | --- | --- | --- |
| 2026-11-27 | Python déterministe sur GitHub Actions (dépôt public, gratuit) | 0 € de budget, Mac pas toujours allumé | Oracle Always Free (risque de récupération), VPS payant |
| 2026-11-27 | Claude ne décide aucun trade | API payante ; LLM non reproductible en backtest | Agent LLM décideur |
| 2026-11-27 | Backtest et paper trading partagent le même code de décision | Éviter les écarts (stop manquant en paper corrigé le 27) | Deux implémentations |
| 2026-11-28 | Plusieurs créneaux cron, un seul cycle par jour UTC | Cron GitHub sauté le 28 | Cron unique |
| 2026-11-28 | Pas de framework externe (Freqtrade, Nautilus) pour l'instant | Notre moteur couvre 1 actif journalier ; ils ajoutent complexité et licences GPL/LGPL | Migration vers Freqtrade |
| 2026-11-28 | Observabilité : journal d'événements JSONL dans le dépôt, puis tableau de bord statique (GitHub Pages) | Gratuit, lisible sur Mac et iPhone, alimenté uniquement par de vrais événements | Serveur temps réel payant |
