# 🔬 Research (Backtests hors-bot)

Ce dossier sert à **tester / valider des stratégies** rapidement, sans toucher au bot Telegram.

Objectif : itérer vite (stratégies, frais, slippage, filtres) puis **n’intégrer dans le bot que ce qui est validé**.

---

## ✅ Stratégies incluses

### BRR — *Bollinger Rejection Range* (15m)

Stratégie mean-reversion orientée **winrate**, avec filtre de régime (range uniquement).

Règles (baseline) :
- Timeframe : **15m**
- Bollinger : **(20, 2.0)**
- Filtre range : **ADX(14) < 18**
- Entrée : wick touche bande + **clôture revient à l’intérieur**
- RSI gate : **<45** (long) / **>55** (short)
- SL : **1.2 × ATR(14)**
- TP : **BB middle** (fixé au moment du signal)
- Time-stop : **12 bougies** (≈ 3h)

---


### VWAP Fade Range (15m)

Mean-reversion orientée winrate qui vise un **retour à la VWAP journalière (UTC)**.

Baseline :
- Timeframe : **15m**
- Filtre range : **ADX(14) < 18**
- VWAP bands : **± 1.0 × ATR(14)**
- Entrée : excès (wick) au-delà de la bande + **clôture revient au-dessus/au-dessous**
- RSI gate : **<45** (long) / **>55** (short)
- SL : **1.0 × ATR(14)**
- TP : **VWAP** (fixée à l’entrée)
- Time-stop : **12 bougies**
- Option : fermeture fin de session (évite le reset VWAP)

### Volatility Breakout Filtered (15m)

Stratégie “plan B” pour les **régimes tendances** (pas optimisée winrate). Utile pour comparer les régimes.

Baseline :
- Donchian : **20**
- Filtre tendance : pente EMA200 + **ADX(14) > 20**
- SL : **1.5 × ATR(14)**
- TP : **3.0 × ATR(14)**
- Time-stop : **48 bougies**

## ▶️ Lancer un backtest

Depuis la racine du projet :

```bash
python research/run_brr_backtest.py --start 2025-01-01 --end 2025-03-31

VWAP Fade :

```bash
python research/run_vwap_fade_backtest.py --start 2025-01-01 --end 2025-03-31
```

Volatility Breakout :

```bash
python research/run_vol_breakout_backtest.py --start 2025-01-01 --end 2025-03-31
```
```

Paramètres utiles :

```bash
python research/run_brr_backtest.py \
  --symbol BTC/USDT \
  --timeframe 15m \
  --start 2025-01-01 \
  --end 2025-12-31 \
  --fee 0.0004 \
  --slippage 0.0002 \
  --risk 0.005 \
  --adx 18 \
  --rsi-long 45 \
  --rsi-short 55 \
  --atr-mult 1.2 \
  --max-hold 12
```

Sorties :
- `research/output/summary_*.json`
- `research/output/trades_*.csv`

---

## ⚠️ Notes importantes

- Le backtest applique une exécution **bougie suivante** (anti-lookahead).
- Les fills intrabougie utilisent `high/low`.
- Si SL et TP sont touchés dans la même bougie : hypothèse **pire cas** (SL en premier).
- Le modèle de fees/slippage est volontairement simple au début (puis on affine).
