# 🔬 Recherche & Backtests (hors bot Telegram)

Ce projet contient un dossier `research/` pour tester des idées **sans toucher au bot**.

Pourquoi ?
- éviter de casser l’UI Telegram pendant les itérations
- accélérer la validation (données, frais, slippage, métriques)
- n’intégrer dans le bot que les stratégies validées

---

## Workflow recommandé

1) Tester une stratégie dans `research/`
2) Valider sur plusieurs périodes + plusieurs hypothèses de frais/slippage
3) Seulement ensuite : intégration “production” dans `strategies/` + backtests Telegram

---

## Backtest BRR (Bollinger Rejection Range)

Script : `research/run_brr_backtest.py`

Exemple :

```bash
python research/run_brr_backtest.py --start 2025-01-01 --end 2025-03-31
```

Le script :
- télécharge les bougies via **CCXT (Binance)**
- calcule les indicateurs (pandas-ta)
- simule une exécution **bougie suivante**
- applique fees + slippage
- exporte un CSV de trades + un résumé JSON

Sorties :
- `research/output/trades_*.csv`
- `research/output/summary_*.json`

---

## Notes importantes

- ⚠️ Retour d’expérience : sur BTC 15m, la baseline BRR peut être négative même sans frais/slippage selon la période. Utiliser BRR surtout comme *benchmark*, pas comme stratégie validée.


- Les backtests `research/` sont “research-grade” : simples, rapides, transparents.
- Les réglages par défaut sont conservateurs pour éviter les faux edges.
- Si SL et TP sont touchés dans la même bougie : hypothèse **pire cas** (SL).


---

## Backtest VWAP Fade Range

Script : `research/run_vwap_fade_backtest.py`

Exemple :

```bash
python research/run_vwap_fade_backtest.py --start 2025-11-01 --end 2026-02-01
```

Notes :
- VWAP calculée par journée UTC (reset à 00:00).
- Baseline : VWAP bands ± **1×ATR**, filtre **ADX < 18**, TP = VWAP.
- Les positions peuvent être fermées en fin de session (option par défaut).

---

## Backtest Volatility Breakout Filtered

Script : `research/run_vol_breakout_backtest.py`

Exemple :

```bash
python research/run_vol_breakout_backtest.py --start 2025-11-01 --end 2026-02-01
```

Notes :
- Stratégie “plan B” pour les phases tendances (comparaison de régime).
- Baseline : Donchian 20 + ADX > 20 + pente EMA200.
