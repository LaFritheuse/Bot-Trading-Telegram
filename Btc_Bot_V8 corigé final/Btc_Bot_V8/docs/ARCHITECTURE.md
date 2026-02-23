# 🏗️ ARCHITECTURE DU PROJET BTC TRADER BOT

## 📋 Vue d'ensemble

Bot de trading Bitcoin automatisé avec interface Telegram, basé sur 3 stratégies de trading et un système de backtest complet (LONG / SHORT / RSI).

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
│
├── research/                # Backtests & recherche hors-bot (non-production)
│   ├── run_brr_backtest.py   # Backtest BRR (Bollinger Rejection Range)
│   └── strategies/           # Stratégies de recherche isolées
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
```

**Callbacks format :**
- `bt_run_720` : Backtest LONG 720h
- `bts_run_720` : Backtest SHORT 720h
- `btr_run_2880` : Backtest RSI 2880 bougies

#### **messages.py** - Textes
```python
Fonctions principales :
- get_dashboard_text() : Texte dashboard
- get_strategies_menu_text() : Texte menu stratégies
- get_strategy_info_text() : Détails Sniper LONG
- get_strategy_short_info_text() : Détails Sniper SHORT
- get_strategy_rsi_info_text() : Détails RSI Bollinger
- get_backtest_duration_menu_text() : Texte sélection durée
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



### Research : stratégies candidates
- `research/run_brr_backtest.py` + `research/strategies/brr_bollinger_rejection_range.py`
- `research/run_vwap_fade_backtest.py` + `research/strategies/vwap_fade_range.py`
- `research/run_vol_breakout_backtest.py` + `research/strategies/volatility_breakout_filtered.py`
