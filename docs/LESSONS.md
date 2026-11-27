# Journal des erreurs et leçons

Une entrée par erreur ou surprise : ce qui s'est passé, la cause, la correction, la règle retenue.
Les plus récentes en haut. Le système ne modifie jamais ses limites de risque à partir de ce journal.

| Date | Constat | Cause | Correction | Règle retenue |
| --- | --- | --- | --- | --- |
| 2026-11-27 | Le paper trading ne vérifiait pas les stops entre deux cycles, contrairement au backtest | Logique de stop codée seulement dans le moteur de backtest | `apply_stop` appliqué sur la dernière barre close à chaque cycle | Backtest et paper trading doivent partager le même code de décision et de sortie |
| 2026-11-27 | Avec la volatilité actuelle (stop 3×ATR ≈ 17 %), aucun achat n'est possible : taille autorisée ≈ 3,7 € < minimum 5 € | 1 € de perte max par trade, facteur gap 1,5 et frais ⇒ stop maximal ≈ 12 % | Aucune (comportement voulu) ; candidates à stop 2×ATR évaluées en fantôme | Ne jamais relâcher une limite pour pouvoir trader ; adapter la stratégie, pas le risque |
| 2026-11-27 | Coinbase a renvoyé 4235 barres BTC au lieu de 4236 à une heure d'intervalle | Source historique non parfaitement stable | Contrôle de validation à chaque téléchargement | Ne jamais supposer qu'une source est immuable ; conserver les données utilisées pour chaque résultat |
| 2026-11-27 | Kraken ne renvoie que ~720 bougies journalières | Limite de l'endpoint OHLC public | Historique long pris chez Coinbase Exchange, Kraken en contrôle | Vérifier la profondeur d'historique de chaque source avant de l'utiliser |
| 2026-11-27 | Taille d'ordre arrondie au centime supérieur : dépassait la perte max par trade de 0,0005 € | `round()` au lieu d'un arrondi vers le bas | `math.floor` sur les centimes | Tout arrondi lié au risque se fait dans le sens prudent |
| 2026-11-27 | Achat régulier (4×5 €) bien meilleur que la stratégie en validation (BTC +95 % contre +17 %) | La stratégie sort souvent du marché et paie 1,8 % par aller-retour | Benchmark ajouté à tous les rapports | Toujours comparer à l'achat régulier, pas seulement au cash et au buy & hold |
| 2026-11-27 | Test final réussi mais gain (+0,78 €) inférieur aux frais payés (2,37 €) | Avantage faible, 21 trades | Aucun réel avant 60 jours de paper trading | Un critère réussi n'est pas une preuve : rapporter la taille de l'échantillon |
