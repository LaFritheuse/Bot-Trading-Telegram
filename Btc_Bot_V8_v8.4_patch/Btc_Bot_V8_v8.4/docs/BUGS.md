# 🐛 BUGS - Historique et résolution

Documentation des bugs rencontrés et corrigés.

---

## ✅ BUGS CORRIGÉS (v8)

### 1) Backtest RSI — callbacks non gérés + moteur manquant
- **Symptômes :** `Callback non géré : btr_run_*` + `AttributeError: backtest_rsi_engine`
- **Correction :** routage des callbacks `btr_run_*` + initialisation de `backtest_rsi_engine`.

### 2) Backtest RSI — erreur KeyError sur Bollinger (`BBU...`)
- **Symptômes :** erreur du type `Erreur Backtest RSI 'BBU...'`
- **Cause :** nom de colonne Bollinger variant selon la lib (ex: `BBU_25_2.0` vs autres formats)
- **Correction :** résolution robuste du nom de colonne (fallback) + message d’erreur lisible.

### 3) Emojis / caractères illisibles dans les logs et messages
- **Symptômes :** `TÃ©lÃ©chargement`, `âŒ`, etc.
- **Correction :** nettoyage des chaînes mal encodées dans les messages/rapports.

---

## 🧹 FONCTIONNALITÉS RETIRÉES (v8)

### Backtest Multi
- **Décision :** option retirée car peu utile vs coût de maintenance (bugs récurrents).
- **Effet :** plus de bouton “Backtest Multi” dans Telegram.
- **Compat :** si un ancien bouton est encore cliqué, le bot affiche un message d’info au lieu de planter.
