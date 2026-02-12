# 🏗️ ARCHITECTURE DU PROJET BTC TRADER BOT

## 📋 Vue d'ensemble

Bot de trading Bitcoin automatisé avec interface Telegram, basé sur 3 stratégies de trading et un système de backtest complet.

---

## 📁 Structure des fichiers

```
btc_bot_final/
│
├── main.py                   # Point d'entrée principal
├── config.py                 # Configuration (TOKEN, CHAT_ID, paramètres)
├── database.py               # Gestion fichier trades.json
├── trading.py                # Moteur de trading temps réel
│
├── strategies/               # Stratégies de trading
│   ├── __init__.py
│   ├── sniper_v11.py        # Stratégie LONG (EMA 200 + Volume)
│   ├── sniper_short_v11.py  # Stratégie SHORT (EMA 200 inverse)
│   └── rsi_bollinger_15m.py # Stratégie RSI + Bollinger Bands
│
├── ui/                       # Interface utilisateur Telegram
│   ├── __init__.py
│   ├── keyboards.py         # Boutons inline (InlineKeyboardMarkup)
│   └── messages.py          # Textes affichés
│
├── handlers/                 # Gestion des interactions Telegram
│   ├── __init__.py
│   ├── commands.py          # Commandes /start, /stop
│   └── callbacks.py         # Gestion callbacks boutons (27 handlers)
│
├── backtest.py              # Moteur backtest LONG
├── backtest_short.py        # Moteur backtest SHORT
├── backtest_rsi.py          # Moteur backtest RSI
├── backtest_multi.py        # Moteur backtest multi-stratégies
│
├── check_deps.py            # Vérification dépendances
├── run.sh / run.bat         # Scripts de lancement
├── requirements.txt         # Dépendances Python
├── .env.example             # Template configuration
├── .gitignore               # Fichiers à ignorer Git
│
├── README.md                # Documentation utilisateur
├── INSTALLATION.md          # Guide installation
│
└── docs/                    # Documentation technique (IA)
    ├── ARCHITECTURE.md      # Ce fichier
    ├── WORKFLOW.md          # Flux d'exécution
    ├── STRATEGIES.md        # Détails stratégies
    ├── CHANGELOG.md         # Historique modifications
    ├── BUGS.md              # Bugs connus/corrigés
    ├── API_REFERENCE.md     # Référence fonctions
    └── README_AI.md         # Guide pour IA
```

---

## 🧩 Modules principaux

### 1. **main.py** - Point d'entrée
```python
Responsabilités :
- Initialisation bot Telegram (Application)
- Enregistrement handlers (commands, callbacks)
- Démarrage job trading automatique (toutes les 1h)
- Boucle d'écoute événements
```

**Flow :**
```
Démarrage → Vérif dépendances → Init Telegram → Enregistrer handlers → 
Start job trading (loop 1h) → Polling updates
```

---

### 2. **config.py** - Configuration
```python
Variables globales :
- TOKEN : Token bot Telegram
- MY_CHAT_ID : ID chat autorisé
- TIMEFRAME : '1h' (unité temps par défaut)
- BACKTEST_INITIAL_CAPITAL : 10000 $ (capital backtest)
- RISK_PER_TRADE : 0.015 (1.5% risque)
- REWARD_RATIO : 3 (ratio SL:TP = 1:3)
- LOG_LEVEL : 'INFO'
```

**Important :** Les stratégies peuvent override certains paramètres (ex: RSI a ses propres RISK/REWARD).

---

### 3. **database.py** - Gestion données
```python
Fichier : trades.json

Structure :
{
    "strategies": {
        "sniper_ema": true,      # Sniper LONG activé
        "sniper_short": true,    # Sniper SHORT activé
        "rsi_bollinger": true    # RSI Bollinger activé
    },
    "trading_mode": "sequential",  # ou "parallel"
    "active_trades": [],           # Trades en cours
    "history": []                  # Historique
}

Méthodes principales :
- load() : Charge trades.json (crée si inexistant)
- save(data) : Sauvegarde trades.json
- toggle_strategy(name) : Active/désactive stratégie
- add_trade(trade) : Ajoute trade actif
- close_trade(id, outcome) : Clôture trade
```

**Migration automatique :** Si anciennes versions manquent `rsi_bollinger`, ajouté automatiquement.

---

### 4. **trading.py** - Moteur temps réel
```python
Classe : TradingEngine

Responsabilités :
- Télécharge données OHLCV toutes les 1h
- Vérifie signaux des stratégies actives
- Place trades (simulation)
- Gère positions ouvertes (check SL/TP)

Flow principal :
1. run() appelé toutes les 1h par job
2. Télécharge 500 dernières bougies
3. Pour chaque stratégie active :
   - Ajoute indicateurs
   - Check signal entry
4. Si signal : Place trade
5. Check trades ouverts : SL/TP atteint ?
6. Close trade si SL/TP touché
```

**Modes :**
- **Sequential** : 1 trade à la fois, premier signal = priorité
- **Parallel** : Chaque stratégie trade indépendamment

---

### 5. **strategies/** - Stratégies de trading

#### Structure commune :
```python
class StrategyName:
    # Paramètres
    RISK_PER_TRADE = 0.015
    REWARD_RATIO = 3
    
    @staticmethod
    def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute indicateurs techniques au DataFrame"""
        
    @staticmethod
    def check_signal(current, previous) -> bool | str:
        """Vérifie si signal d'entrée (LONG/SHORT)"""
        
    @staticmethod
    def calculate_levels(entry_price, signal=None) -> dict:
        """Calcule SL/TP"""
        return {'stop_loss': ..., 'take_profit': ...}
```

**Stratégies :**
1. **sniper_v11.py** : LONG sur breakout EMA 200 + volume
2. **sniper_short_v11.py** : SHORT sur breakout inverse
3. **rsi_bollinger_15m.py** : Retournements zones extrêmes (survente/surachat)

Voir `docs/STRATEGIES.md` pour détails.

---

### 6. **ui/** - Interface utilisateur

#### **keyboards.py** - Boutons interactifs
```python
Fonctions principales :
- get_main_keyboard() : Dashboard principal
- get_strategies_keyboard(sniper, short, rsi) : Menu stratégies
- get_info_keyboard() : Info stratégie LONG
- get_info_short_keyboard() : Info stratégie SHORT
- get_info_rsi_keyboard() : Info stratégie RSI
- get_backtest_duration_keyboard() : Durée backtest LONG
- get_backtest_duration_short_keyboard() : Durée backtest SHORT
- get_backtest_duration_rsi_keyboard() : Durée backtest RSI
- get_backtest_multi_selection_keyboard(s, sh, r) : Sélection stratégies multi
- get_backtest_multi_mode_keyboard() : Mode séquentiel/parallèle
```

**Callbacks format :**
- `bt_run_720` : Backtest LONG 720h
- `bts_run_720` : Backtest SHORT 720h
- `btr_run_2880` : Backtest RSI 2880 bougies
- `btm_run_720` : Backtest multi 720h
- `btm_toggle_sniper` : Toggle Sniper dans multi

#### **messages.py** - Textes
```python
Fonctions principales :
- get_dashboard_text() : Texte dashboard
- get_strategies_menu_text() : Texte menu stratégies
- get_strategy_info_text() : Détails Sniper LONG
- get_strategy_short_info_text() : Détails Sniper SHORT
- get_strategy_rsi_info_text() : Détails RSI Bollinger
- get_backtest_duration_menu_text() : Texte sélection durée
- get_backtest_multi_selection_text() : Texte sélection multi
```

---

### 7. **handlers/** - Gestion interactions

#### **commands.py** - Commandes Telegram
```python
/start : Affiche dashboard principal
/stop : Demande confirmation arrêt bot
```

#### **callbacks.py** - Gestion boutons (27 handlers)
```python
Classe : CallbackHandler

Méthodes __init__ :
- backtest_engine : BacktestEngine (LONG)
- backtest_short_engine : BacktestShortEngine (SHORT)
- backtest_rsi_engine : BacktestRSIEngine (RSI)
- backtest_multi_engine : BacktestMultiEngine
- user_state : Dict[chat_id, state] (inputs personnalisés)

Handlers principaux :
Navigation :
- _handle_back_to_dash() : Retour dashboard
- _handle_strategies_menu() : Menu stratégies
- _handle_history() : Historique trades

Stratégies :
- _handle_toggle_sniper() : Toggle LONG
- _handle_toggle_short() : Toggle SHORT
- _handle_toggle_rsi() : Toggle RSI
- _handle_strategy_info() : Info LONG
- _handle_strategy_short_info() : Info SHORT
- _handle_strategy_rsi_info() : Info RSI

Backtests solo :
- _handle_backtest_duration_menu() : Menu durée LONG
- _handle_backtest_duration_short_menu() : Menu durée SHORT
- _handle_backtest_duration_rsi_menu() : Menu durée RSI
- _handle_run_backtest(query, context, data) : Lance backtest LONG
- _handle_run_backtest_short(query, context, data) : Lance backtest SHORT
- _handle_run_backtest_rsi(query, context, data) : Lance backtest RSI

Backtests multi :
- _handle_backtest_multi_menu() : Menu sélection stratégies
- _handle_btm_toggle_sniper() : Toggle LONG dans multi
- _handle_btm_toggle_short() : Toggle SHORT dans multi
- _handle_btm_toggle_rsi() : Toggle RSI dans multi
- _handle_btm_next() : Passer au choix mode
- _handle_btm_mode_sequential() : Mode séquentiel
- _handle_btm_mode_parallel() : Mode parallèle
- _handle_run_backtest_multi() : Lance backtest multi

Inputs personnalisés :
- _handle_custom_backtest_input() : Input perso LONG
- _handle_custom_backtest_short_input() : Input perso SHORT
- _handle_custom_backtest_rsi_input() : Input perso RSI
- _process_backtest_hours() : Traite input LONG
- _process_backtest_short_hours() : Traite input SHORT
- _process_backtest_rsi_candles() : Traite input RSI

Contrôle :
- _handle_ask_stop() : Demande confirmation stop
- _handle_confirm_stop() : Arrête bot
```

**Flow callbacks :**
```
User click button → Telegram webhook → handle_callback() → 
Route par callback_data → Appel handler spécifique → 
Edit message avec nouveau texte/keyboard
```

---

### 8. **backtest*.py** - Moteurs backtest

#### **backtest.py** - Backtest LONG
```python
Classe : BacktestEngine

Méthodes :
- fetch_historical_data(hours) : Télécharge X heures
- run_simulation(df) : Simule trades sur données
- run_backtest(hours, progress_callback) : Lance backtest complet
- _format_report(hours, results) : Formate résultat
```

#### **backtest_short.py** - Backtest SHORT
Identique à backtest.py mais pour SniperShortV11Strategy

#### **backtest_rsi.py** - Backtest RSI
Identique mais :
- Timeframe 15min (pas 1h)
- Paramètre en **bougies** (pas heures)

#### **backtest_multi.py** - Backtest multi
```python
Classe : BacktestMultiEngine

Modes :
- run_simulation_sequential(df, strats) : 1 trade à la fois
- run_simulation_parallel(df, strats) : Trades simultanés

Important :
- Mode séquentiel : Capital partagé, premier signal prioritaire
- Mode parallèle : Chaque stratégie a capital complet
```

**Correction importante (v7.4) :**
Tous les backtests utilisent maintenant `high`/`low` pour détecter SL/TP (pas juste `close`).

---

## 🔄 Flow d'exécution global

### Démarrage bot :
```
main.py → check_deps.py → Init Telegram Application → 
Register handlers (commands, callbacks) → 
Start job trading (run TradingEngine every 1h) → 
Start polling
```

### Trading automatique (toutes les 1h) :
```
TradingEngine.run() → Fetch OHLCV → 
For each active strategy:
    Add indicators → Check signal → 
    If signal: Place trade → Save to DB
Check open trades:
    If SL/TP hit: Close trade → Update DB
```

### Interaction utilisateur :
```
User click button → Telegram callback → 
CallbackHandler.handle_callback() → 
Route to specific handler → 
Handler processes → 
Edit message with new text/keyboard
```

### Backtest :
```
User selects duration → Handler calls BacktestEngine → 
Fetch historical data → Add indicators → 
Simulate trades (check signal → place → check SL/TP) → 
Calculate metrics (WR, P&L) → 
Format report → Display to user
```

---

## 📊 Dépendances externes

```python
ccxt==4.4.52           # API Binance
python-telegram-bot==20.7  # Bot Telegram
pandas==2.2.3          # DataFrames
pandas_ta==0.3.14b     # Indicateurs techniques
python-dotenv==1.0.1   # Variables .env
```

---

## 🔐 Sécurité

- **Authentification** : Seul MY_CHAT_ID peut interagir
- **Papier trading** : Mode simulation par défaut
- **Gestion risque** : Max 1.5% par trade
- **Rate limiting** : 0.05s entre requêtes API Binance

---

## 🎯 Points d'extension

**Ajouter une stratégie :**
1. Créer fichier `strategies/ma_strategie.py`
2. Implémenter méthodes : `add_indicators`, `check_signal`, `calculate_levels`
3. Ajouter dans `trading.py` : `self.strategies['ma_strat'] = MaStrategie`
4. Ajouter dans `database.py` : clé dans `strategies`
5. Créer backtest : `backtest_ma_strat.py`
6. Ajouter UI : keyboards + messages + handlers

**Ajouter un indicateur :**
1. Importer dans stratégie : `import pandas_ta as ta`
2. Ajouter dans `add_indicators()` : `df['mon_indic'] = ta.mon_indic(...)`
3. Utiliser dans `check_signal()`

---

**Version :** 7.4  
**Dernière mise à jour :** 11 Février 2026  
**Auteur :** Mec + Claude
