# 📝 CHANGELOG - BTC TRADER BOT

## 2026-02-23 — Robustesse & Sécurité (v8.3) — Audit Claude

### Contexte
Groupe 3 des corrections issues de l'audit. Corrections transversales : sécurité accès, intégrité données, maintenance logs.

---

### 🐛 BUGS CORRIGÉS

#### 1. [CRITIQUE] Aucun contrôle owner-only — n'importe qui pouvait piloter le bot
**Fichiers :** `handlers/callbacks.py`, `handlers/commands.py`
**Symptôme :** Tout utilisateur Telegram connaissant le lien du bot pouvait interagir : stopper le bot, toggler les stratégies, lancer des backtests. Aucune vérification d'identité.
**Correction :**
```python
# handlers/commands.py — commande /start
if update.message.chat_id != MY_CHAT_ID:
    logger.warning(f"Accès non autorisé refusé (chat_id={update.message.chat_id})")
    return

# handlers/callbacks.py — boutons inline
if query.message.chat_id != MY_CHAT_ID:
    logger.warning(f"Callback non autorisé refusé (chat_id={query.message.chat_id})")
    return

# handlers/callbacks.py — messages texte
if chat_id != MY_CHAT_ID:
    logger.warning(f"Message non autorisé refusé (chat_id={chat_id})")
    return
```

#### 2. [CRITIQUE] DB JSON non atomique — risque corruption au crash
**Fichier :** `database.py`
**Symptôme :** L'écriture directe dans `trades.json` laissait une fenêtre de corruption : si le processus crashait pendant `json.dump()`, le fichier était tronqué et illisible. Perte de tout l'historique possible.
**Correction — tmp + os.replace() atomique :**
```python
# AVANT (buggé)
with open(self.db_path, 'w') as f:
    json.dump(data, f, indent=4)

# APRÈS (atomique)
with tempfile.NamedTemporaryFile(mode='w', dir=dir_path, suffix='.tmp', delete=False) as tmp_file:
    json.dump(data, tmp_file, indent=4)
    tmp_path = tmp_file.name
os.replace(tmp_path, self.db_path)  # Rename atomique — garanti indivisible par l'OS
```

#### 3. [MINEUR] Logs sans rotation — bot.log grossissait indéfiniment
**Fichier :** `main.py`
**Symptôme :** `logging.basicConfig()` avec `FileHandler` standard → `bot.log` croissait sans limite, potentiellement remplissant le disque sur serveur VPS.
**Correction :**
```python
# AVANT
logging.basicConfig(handlers=[logging.FileHandler('bot.log'), ...])

# APRÈS (max 5 MB × 3 fichiers = 15 MB max)
from logging.handlers import RotatingFileHandler
rotating_handler = RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=3)
logging.basicConfig(handlers=[rotating_handler, logging.StreamHandler(sys.stdout)])
```

---

### 📁 Fichiers modifiés (Groupe 3)
- `main.py` (bug 3 : rotation logs)
- `database.py` (bug 2 : écriture atomique)
- `handlers/commands.py` (bug 1 : owner-only /start)
- `handlers/callbacks.py` (bug 1 : owner-only callbacks + messages)

---

## 2026-02-23 — Corrections backtests SHORT et RSI (v8.2) — Audit Claude

### Contexte
Groupe 2 des corrections issues de l'audit indépendant.
Deux bugs détectés dans les moteurs de backtest, dont un non signalé par ChatGPT.

---

### 🐛 BUGS CORRIGÉS

#### 1. [CRITIQUE] `backtest_short.py` utilisait encore `close` pour détecter SL/TP
**Fichier :** `backtest_short.py`
**Symptôme :** Le fix annoncé dans le CHANGELOG v8 ("Uniformisation : TOUS les backtests utilisent high/low") n'avait **pas été appliqué** à `backtest_short.py`. Ce fichier appelait `SniperShortV11Strategy.check_exit(future_candle['close'], ...)` qui compare avec `close`, ratant tous les SL/TP touchés intra-bougie si le prix revenait avant clôture. Résultats SHORT trop optimistes.
**Correction :**
```python
# AVANT (buggé — check_exit utilise close)
exit_result = SniperShortV11Strategy.check_exit(future_candle['close'], temp_trade)

# APRÈS (correct — symétrie avec backtest.py)
# SHORT : SL si high >= stop_loss | TP si low <= take_profit
if future_candle['high'] >= levels['stop_loss']:
    outcome = "LOSS"
elif future_candle['low'] <= levels['take_profit']:
    outcome = "WIN"
```

#### 2. [CRITIQUE] `backtest_rsi.py` — trades SHORT toujours LOSS immédiatement
**Fichier :** `backtest_rsi.py`  
**Non signalé par ChatGPT.**
**Symptôme :** La vérification SL/TP ne tenait pas compte de la direction du trade. Pour un SHORT (SL au-dessus de l'entrée, TP en dessous) :
- `future_candle['low'] <= stop_loss` était presque toujours True dès la bougie suivante (le low, autour du prix actuel, est presque toujours ≤ au SL qui est 1.5% au-dessus) → LOSS immédiat garanti.
- Résultat : tous les trades SHORT du backtest RSI comptaient comme des pertes immédiates, faussant complètement le win rate et le P&L.

**Preuve :**
```
SHORT entry=100000, SL=101500, TP=95500
Bougie suivante typique : low=99500, high=100500

Ancienne vérif : low(99500) <= SL(101500) → LOSS immédiat ← FAUX
Correcte SHORT : high(100500) >= SL(101500) → False (trade encore ouvert)
```

**Correction — symétrie directionnelle :**
```python
if signal == "LONG":
    if future_candle['low']  <= levels['stop_loss']:   outcome = "LOSS"
    elif future_candle['high'] >= levels['take_profit']: outcome = "WIN"
else:  # SHORT
    if future_candle['high'] >= levels['stop_loss']:   outcome = "LOSS"
    elif future_candle['low']  <= levels['take_profit']: outcome = "WIN"
```

---

### 📁 Fichiers modifiés (Groupe 2)
- `backtest_short.py` (bug 1)
- `backtest_rsi.py` (bug 2)

### ✅ Fichiers NON modifiés (Groupe 2)
- `backtest.py` — déjà correct
- `trading.py` — corrigé Groupe 1
- `strategies/` — corrigé Groupe 1
- `ui/` — non touché
- `handlers/` — non touché
- `database.py` — sera corrigé Groupe 3

---

## 2026-02-23 — Corrections critiques live trading (v8.1) — Audit Claude

### Contexte
Audit indépendant réalisé par Claude après comparaison avec un audit ChatGPT.
5 bugs supplémentaires identifiés non détectés par le premier audit.
Ce bloc documente les corrections du **Groupe 1** (trading live + signal RSI).

---

### 🐛 BUGS CORRIGÉS

#### 1. [CRITIQUE] `check_signal` RSI utilisait `close` au lieu de `low/high`
**Fichier :** `strategies/rsi_bollinger_15m.py`
**Symptôme :** Le signal LONG se déclenchait uniquement si la bougie *clôturait* sous la bande inférieure. Les wicks touchant la bande et revenant à l'intérieur (le pattern mean-reversion le plus fort) n'étaient jamais détectés.
**Correction :**
```python
# AVANT (buggé)
if close <= bb_lower and rsi < 30 ...   # rate les wicks

# APRÈS (correct)
if low <= bb_lower and rsi < 30 ...     # détecte le toucher réel
if high >= bb_upper and rsi > 70 ...    # idem pour SHORT
```

#### 2. [CRITIQUE] `TypeError` garanti dès le premier signal RSI en live
**Fichier :** `trading.py` → `_enter_position`
**Symptôme :** `RSIBollingerStrategy.create_trade_entry` exige 4 paramètres (dont `direction`) mais `_enter_position` l'appelait avec 3. Crash immédiat à chaque signal RSI.
**Correction :** `_enter_position` accepte maintenant `direction` en paramètre et le transmet à `create_trade_entry` pour RSI. Les stratégies Sniper gardent leur signature à 3 paramètres (direction implicite par design).

#### 3. [CRITIQUE] Direction du signal RSI non propagée dans le flux
**Fichier :** `trading.py` → `_check_for_entry`
**Symptôme :** `check_signal` retourne `"LONG"` ou `"SHORT"` mais le code ne capturait pas cette valeur de retour. Même en corrigeant le bug n°2, la direction aurait été perdue.
**Correction :** Le signal est maintenant capturé :
```python
# AVANT
if StrategyClass.check_signal(last, prev):  # valeur perdue
    await self._enter_position(...)

# APRÈS
signal = StrategyClass.check_signal(last, prev)
if signal:
    direction = signal if isinstance(signal, str) else ("SHORT" if strat_key == 'sniper_short' else "LONG")
    await self._enter_position(..., direction)
```

#### 4. [CRITIQUE] Mauvaise classe utilisée pour gérer les positions RSI ouvertes
**Fichier :** `trading.py` → `_manage_open_position`
**Symptôme :** La sélection de classe se basait sur `'SHORT' in strategy_name`. Les trades RSI (nom : `"RSI Bollinger 15min"`) ne contiennent pas `'SHORT'`, donc *tous* les trades RSI utilisaient `SniperV11Strategy.check_exit()`, qui ne connaît pas le champ `direction`. Les trades RSI SHORT étaient vérifiés dans le mauvais sens.
**Correction :**
```python
# AVANT
if 'SHORT' in strategy_name:
    StrategyClass = SniperShortV11Strategy
else:
    StrategyClass = SniperV11Strategy  # ← appliqué à tort aux trades RSI

# APRÈS
if strategy_name == RSIBollingerStrategy.NAME:
    StrategyClass = RSIBollingerStrategy
elif 'SHORT' in strategy_name:
    StrategyClass = SniperShortV11Strategy
else:
    StrategyClass = SniperV11Strategy
```

#### 5. [CRITIQUE] RSI tournait sur des données 1h au lieu de 15m en live
**Fichier :** `trading.py` → `_check_for_entry` + nouvelle méthode `_fetch_market_data_15m`
**Symptôme :** `_fetch_market_data` télécharge des bougies `TIMEFRAME` (1h) pour toutes les stratégies. RSI Bollinger est conçu, documenté et backtesté sur 15m. En live, il analysait des bougies 4x plus lentes.
**Correction :** Ajout de `_fetch_market_data_15m()` qui télécharge 200 bougies 15m. `_check_for_entry` utilise ce fetch dédié pour RSI.

#### 6. [MINEUR] `RSIBollingerStrategy` absent de `self.strategies` dans `TradingEngine.__init__`
**Fichier :** `trading.py`
**Symptôme :** Le dictionnaire `self.strategies` ne contenait pas `'rsi_bollinger'`. Non utilisé dans le flow actuel mais bombe à retardement pour tout refactor.
**Correction :** RSI ajouté au mapping.

---

### 📁 Fichiers modifiés
- `strategies/rsi_bollinger_15m.py` (bug 1)
- `trading.py` (bugs 2, 3, 4, 5, 6)

### ✅ Fichiers NON modifiés (Groupe 1)
- `backtest.py` — non touché
- `backtest_short.py` — sera corrigé Groupe 2
- `backtest_rsi.py` — non touché
- `ui/` — non touché (aucun changement visuel)
- `handlers/` — non touché
- `database.py` — sera corrigé Groupe 3
- `config.py` — non touché

---

## 2026-02-13 — Research : nouveaux candidats (VWAP Fade / Volatility Breakout)

### Ajouté
- Stratégie research `VWAP Fade Range` (retour à la VWAP, filtre range) :
  - script `research/run_vwap_fade_backtest.py`
  - module `research/strategies/vwap_fade_range.py`
- Stratégie research `Volatility Breakout Filtered` (plan B tendance) :
  - script `research/run_vol_breakout_backtest.py`
  - module `research/strategies/volatility_breakout_filtered.py`

### Doc
- Mise à jour de `docs/RESEARCH.md` et `research/README.md`

## 2026-02-13 — Module Research (backtests hors-bot)

### Ajouté
- Dossier `research/` pour tester des stratégies **sans toucher au bot Telegram**.
- Script `research/run_brr_backtest.py` (baseline BRR Bollinger Rejection Range, 15m) :
  - download OHLCV via CCXT (Binance)
  - exécution **bougie suivante** (anti-lookahead)
  - prise en compte fees + slippage
  - export des trades (CSV) + résumé (JSON)
- Documentation : `docs/RESEARCH.md`

## 2026-02-13 — Btc_Bot_V8 : simplification (retrait Backtest Multi)

### Changé
- Retrait complet de l'option **Backtest Multi** (bouton Telegram + callbacks) pour réduire la maintenance et éviter des bugs récurrents.
- Suppression du module `backtest_multi.py` devenu inutile.

### Notes
- Les backtests **LONG / SHORT / RSI** restent inchangés.
- Si un ancien message Telegram contient encore un bouton "Backtest Multi", le bot affiche maintenant un message d'information au lieu de planter.

---

## 2026-02-13 — Corrections backtests (RSI)

### Corrigé
- Backtest RSI Bollinger : prise en charge des callbacks `btr_run_*` et initialisation de `backtest_rsi_engine` (plus de "Callback non géré" / `AttributeError`).
- UI : suppression des parenthèses "(2880)/(17280)/(35040)" dans les boutons de durée RSI.
- Texte/Emojis : réparation de plusieurs chaînes mojibake (ex: `reçu` → `reçu`, emojis cassés) dans le code et la doc.
- Backtest RSI Bollinger : sélection robuste des colonnes Bollinger (BBU/BBM/BBL) pour éviter les KeyError liés au format (ex: `BBU_25_2` vs `BBU_25_2.0`) + affichage des erreurs en bloc code pour préserver les underscores.

Historique détaillé de toutes les modifications du projet.

---

## 🆕 Version 7.4 FINAL - 11 Février 2026

### ✅ Corrections majeures

#### 1. 🐛 BUG CRITIQUE - Incohérence backtest solo vs multi
**Problème :**
- Résultats différents entre `backtest.py` (solo) et `backtest_multi.py`
- Exemple : Même stratégie, même période → Win Rate différent

**Cause identifiée :**
```python
# backtest.py (CORRECT)
if future_candle['low'] <= levels['stop_loss']:  # ✅ Utilise LOW
    outcome = "LOSS"
elif future_candle['high'] >= levels['take_profit']:  # ✅ Utilise HIGH
    outcome = "WIN"

# backtest_multi.py (INCORRECT v7.3)
exit_result = StrategyClass.check_exit(future_candle['close'], trade)  # ❌ Utilise CLOSE
```

**Solution (v8) :**
- Uniformisation : TOUS les backtests utilisent `high`/`low`
- Note v8.1 : Ce fix n'avait pas été appliqué à `backtest_short.py` — corrigé en Groupe 2.

#### 2. 🎨 Emojis cassés dans l'interface
**Problème :**
- Emojis affichés comme `ðŸŸ¢` au lieu de 🟢
- Cause : Encoding UTF-8 corrompu lors du premier upload

**Solution :**
- Remplacement bytes corrompus par vrais emojis UTF-8

#### 3. ❌ Handlers manquants dans callbacks.py
- 6 handlers RSI déclarés mais non créés → ajoutés

#### 4. 🔧 get_strategies_keyboard() - Mauvais nombre d'arguments
- Signature mise à jour pour 3 paramètres

---

## 📋 Version 7.3 - 10 Février 2026

### Fonctionnalités initiales

#### Stratégies
- ✅ Sniper V11 LONG (EMA 200 + Volume)
- ✅ Sniper V11 SHORT (EMA 200 inverse)

#### Trading
- ✅ Moteur trading temps réel
- ✅ Gestion risque 1.5% / Ratio 3:1
- ✅ 2 modes : Séquentiel / Parallèle

#### Backtest
- ✅ Backtest solo LONG
- ✅ Backtest solo SHORT
- ✅ Backtest multi (compare 2 stratégies)

#### Interface
- ✅ Bot Telegram complet
- ✅ Dashboard performances
- ✅ Toggle stratégies on/off
- ✅ Historique trades

#### Bugs connus (v7.3)
- ❌ Backtest multi utilise `close` au lieu de `high`/`low`
- ❌ Emojis cassés partout
- ❌ Pas de stratégie RSI

---

## 🎯 Roadmap (todo)

### Groupe 2 (backtests) — ✅ FAIT
- [x] `backtest_short.py` : high/low correct (fix v8 non appliqué à ce fichier)
- [x] `backtest_rsi.py` : correction direction-aware SL/TP (LOSS immédiat sur tous les SHORT)

### Groupe 3 (robustesse)
- [ ] Contrôle `chat_id == MY_CHAT_ID` dans tous les handlers
- [ ] DB atomique (tmp + rename)
- [ ] `RotatingFileHandler` pour bot.log
- [ ] `asyncio.to_thread` pour appels CCXT bloquants

---

**Auteur :** Mec + Claude (Anthropic)
**Dernière mise à jour :** 23 Février 2026
**Version actuelle :** 8.1 (Groupe 1 corrigé)
