# 🤖 GUIDE POUR IA - BTC TRADER BOT

Ce document permet à n'importe quelle IA de comprendre rapidement le projet et y contribuer.

---

## 🎯 Objectif du projet

Bot de trading Bitcoin automatisé avec interface Telegram.
- **3 stratégies** de trading (LONG 1H, SHORT 1H, RSI 15min)
- **3 moteurs** de backtest (LONG / SHORT / RSI)
- **Interface Telegram** complète (27 handlers)
- **Gestion risque** : 1.5% par trade, ratio 1:3

---

## 📁 Navigation rapide

```
docs/
├── ARCHITECTURE.md     ← Structure complète du projet
├── STRATEGIES.md       ← Détails des 3 stratégies
├── CHANGELOG.md        ← Historique modifications
├── BUGS.md             ← Bugs connus/corrigés
└── README_AI.md        ← Ce fichier

Code source :
├── main.py             ← Point d'entrée
├── trading.py          ← Moteur trading temps réel
├── strategies/         ← 3 stratégies
├── ui/                 ← Interface Telegram
├── handlers/           ← Gestion interactions
└── backtest*.py        ← 3 moteurs backtest

Recherche (hors-bot) :
└── research/           ← backtests / validations rapides
```

---

## 🚀 Démarrage rapide pour IA

### 1. Lire d'abord
```
1. Ce fichier (README_AI.md)          ← Vue d'ensemble
2. docs/ARCHITECTURE.md               ← Structure détaillée
3. docs/STRATEGIES.md                 ← Logique stratégies
```

### 2. Fichiers clés à connaître
```python
config.py        # Paramètres globaux
database.py      # Gestion trades.json
trading.py       # Moteur temps réel
handlers/callbacks.py  # 27 handlers Telegram (gros fichier !)
```

### 3. Points d'attention
```
⚠️ HIGH/LOW vs CLOSE dans backtests (bug corrigé v8)
⚠️ Encoding UTF-8 pour emojis
⚠️ Timeframe différent : 1H (Sniper) vs 15min (RSI)
⚠️ RSI retourne str ("LONG"/"SHORT") pas bool
```

---

## 🔧 Tâches courantes

### Ajouter une stratégie
```python
# 1. Créer strategies/ma_strat.py
class MaStrategie:
    RISK_PER_TRADE = 0.015
    REWARD_RATIO = 3
    
    @staticmethod
    def add_indicators(df): ...
    
    @staticmethod
    def check_signal(current, previous): ...
    
    @staticmethod
    def calculate_levels(entry, signal=None): ...

# 2. Intégrer dans trading.py
from strategies.ma_strat import MaStrategie
self.strategies['ma_strat'] = MaStrategie

# 3. Ajouter dans database.py
"ma_strat": True

# 4. Créer backtest_ma_strat.py
# 5. UI : keyboards.py + messages.py + callbacks.py
```

### Corriger un bug
```python
# 1. Identifier fichier + ligne (voir docs/BUGS.md)
# 2. Vérifier syntaxe Python
python3 -m py_compile fichier.py

# 3. Tester dans Telegram
python3 main.py

# 4. Documenter dans docs/BUGS.md et CHANGELOG.md
```

### Modifier l'interface
```python
# Boutons : ui/keyboards.py
def get_mon_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Label", callback_data='mon_callback')]
    ])

# Textes : ui/messages.py
def get_mon_text():
    return "🤖 **Mon texte**\n\nDescription..."

# Gestion clic : handlers/callbacks.py
async def _handle_mon_callback(self, query, context):
    await query.edit_message_text(
        text=get_mon_text(),
        reply_markup=get_mon_keyboard()
    )

# Enregistrer : callbacks.py → handlers dict
'mon_callback': self._handle_mon_callback,
```

---

## 🧩 Architecture en 5 points

### 1. **Stratégies** (`strategies/`)
```python
Responsabilité : Logique de trading
Méthodes clés :
- add_indicators(df) : Ajoute indicateurs techniques
- check_signal(current, previous) : Détecte signal entry
- calculate_levels(entry, signal) : Calcule SL/TP
```

### 2. **Trading** (`trading.py`)
```python
Responsabilité : Exécution automatique
Flow :
1. Fetch OHLCV toutes les 1h (job)
2. Check signals stratégies actives
3. Place trades si signal
4. Monitor positions (SL/TP)
```

### 3. **Backtest** (`backtest*.py`)
```python
Responsabilité : Simulation historique
3 moteurs :
- backtest.py : LONG solo
- backtest_short.py : SHORT solo
- backtest_rsi.py : RSI solo
```

### 4. **Interface** (`ui/` + `handlers/`)
```python
Responsabilité : Interaction Telegram
Fichiers :
- ui/keyboards.py : Boutons (InlineKeyboardMarkup)
- ui/messages.py : Textes affichés
- handlers/commands.py : Commandes /start /stop
- handlers/callbacks.py : Gestion clics (27 handlers)
```

### 5. **Données** (`database.py`)
```python
Responsabilité : Persistance trades.json
Structure :
{
  "strategies": {"sniper_ema": true, "sniper_short": true, "rsi_bollinger": true},
  "trading_mode": "sequential",
  "active_trades": [],
  "history": []
}
```

---

## 🐛 Bugs les plus fréquents

### 1. Handler manquant
```python
# Symptôme
AttributeError: 'CallbackHandler' object has no attribute '_handle_X'

# Cause
Handler déclaré dans routeur mais fonction non créée

# Solution
Créer la fonction async def _handle_X(self, query, context)
```

### 2. Arguments fonction
```python
# Symptôme
TypeError: fonction() missing 1 required positional argument

# Cause
Signature fonction modifiée mais appels non mis à jour

# Solution
Chercher tous les appels : grep -r "fonction(" .
```

### 3. HIGH/LOW vs CLOSE
```python
# Symptôme
Backtests incohérents

# Cause
Utilisation de 'close' pour détecter SL/TP

# Solution
Toujours utiliser 'high' et 'low'
if candle['low'] <= sl: ...
if candle['high'] >= tp: ...
```

### 4. Emojis cassés
```python
# Symptôme
ðŸŸ¢ au lieu de 🟢

# Cause
Encoding UTF-8 corrompu

# Solution
Écrire fichiers avec encoding='utf-8' explicite
Ou remplacer bytes corrompus par vrais emojis
```

---

## 📊 Données importantes

### Paramètres globaux (config.py)
```python
TOKEN = os.getenv('TELEGRAM_TOKEN')
MY_CHAT_ID = os.getenv('MY_CHAT_ID')
TIMEFRAME = '1h'
BACKTEST_INITIAL_CAPITAL = 10000
RISK_PER_TRADE = 0.015  # 1.5%
REWARD_RATIO = 3        # TP = 3x SL
```

### Structure trade
```python
{
    'id': 'uuid',
    'strategy': 'sniper_ema',
    'entry_price': 100000.0,
    'stop_loss': 98500.0,
    'take_profit': 104500.0,
    'timestamp': 'ISO8601',
    'signal': 'LONG'  # ou 'SHORT'
}
```

### Callbacks format
```python
# Backtest LONG
'bt_run_720'  → 720 heures

# Backtest SHORT
'bts_run_720' → 720 heures

# Backtest RSI
'btr_run_2880' → 2880 bougies 15min

```

---

## 🎓 Concepts clés

### Timeframes
```
Sniper LONG  : 1H (1 bougie = 1 heure)
Sniper SHORT : 1H (1 bougie = 1 heure)
RSI Bollinger: 15MIN (1 bougie = 15 minutes)
```

### Modes trading multi
```
SÉQUENTIEL :
- 1 trade à la fois
- Capital partagé entre stratégies
- Premier signal = prioritaire

PARALLÈLE :
- Trades simultanés
- Chaque stratégie a capital COMPLET
- Résultats cumulés
```

### Détection SL/TP
```python
# CORRECT (v8+)
if future_candle['low'] <= stop_loss:
    outcome = "LOSS"
elif future_candle['high'] >= take_profit:
    outcome = "WIN"

# INCORRECT (v7.3)
if future_candle['close'] <= stop_loss:  # ❌ Rate SL pendant bougie
```

---

## 🔍 Debugging tips

### Vérifier syntaxe
```bash
python3 -m py_compile fichier.py
```

### Tester imports
```python
python3 << 'EOF'
import sys
sys.path.insert(0, '/path/to/project')
from strategies.sniper_v11 import SniperV11Strategy
print("✅ Import OK")
EOF
```

### Logs détaillés
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Variable: {variable}")
```

### Tester handlers
```python
# Lister tous handlers déclarés
grep "'.*': self._handle" handlers/callbacks.py

# Vérifier fonctions définies
grep "async def _handle" handlers/callbacks.py

# Comparer : déclarés vs définis
```

---

## 📚 Ressources

### Documentation interne
- `docs/ARCHITECTURE.md` - Structure complète
- `docs/STRATEGIES.md` - Détails stratégies
- `docs/CHANGELOG.md` - Historique modifications
- `docs/BUGS.md` - Bugs connus/corrigés
- `README.md` - Documentation utilisateur
- `INSTALLATION.md` - Guide installation

### Dépendances
- ccxt : API Binance
- python-telegram-bot : Bot Telegram
- pandas : DataFrames
- pandas_ta : Indicateurs techniques

### Liens utiles
- Telegram Bot API : https://core.telegram.org/bots/api
- ccxt docs : https://docs.ccxt.com/
- pandas_ta : https://github.com/twopirllc/pandas-ta

---

## ✅ Checklist contribution

Avant de modifier le code :
- [ ] Lire docs/ARCHITECTURE.md
- [ ] Comprendre le flow d'exécution
- [ ] Identifier fichiers à modifier

Pendant modification :
- [ ] Respecter structure existante
- [ ] Ajouter type hints
- [ ] Logs pour debug
- [ ] Gérer exceptions (try/except)

Après modification :
- [ ] Vérifier syntaxe : `python3 -m py_compile`
- [ ] Tester manuellement dans Telegram
- [ ] Mettre à jour CHANGELOG.md
- [ ] Mettre à jour BUGS.md si bug fix
- [ ] Documenter dans code (docstrings)

---

## 🎯 Questions fréquentes IA

**Q : Où ajouter un nouveau bouton ?**  
A : `ui/keyboards.py` + handler dans `handlers/callbacks.py`

**Q : Comment modifier un texte affiché ?**  
A : `ui/messages.py`

**Q : Où est la logique de trading ?**  
A : `trading.py` (temps réel) + `strategies/` (logique)

**Q : Comment créer un backtest ?**  
A : Copier `backtest.py` et adapter pour nouvelle stratégie

**Q : Tous les handlers sont où ?**  
A : `handlers/callbacks.py` - classe CallbackHandler (27 handlers)

**Q : Pourquoi backtests incohérents ?**  
A : Vérifier utilisation `high`/`low` (pas `close`)

**Q : Emojis cassés ?**  
A : Problème encoding UTF-8, voir docs/BUGS.md

**Q : Comment tester sans Telegram ?**  
A : Impossible, bot nécessite TOKEN. Utiliser bot test.

---

## 🚨 Points critiques à ne PAS casser

1. ✅ **HIGH/LOW dans backtests** (pas close)
2. ✅ **Encoding UTF-8** pour emojis
3. ✅ **27 handlers** déclarés = 27 définis
4. ✅ **Type hints** pour check_signal (bool vs str)
5. ✅ **Timeframe** : 1H (Sniper) vs 15min (RSI)

---

## 📝 Template contribution

```markdown
## [Type] Titre court

**Fichiers modifiés :**
- fichier1.py (ligne X)
- fichier2.py (ligne Y)

**Changements :**
- Ajout feature X
- Correction bug Y

**Tests :**
- [ ] Syntaxe Python OK
- [ ] Tests manuels OK
- [ ] Logs sans erreur

**Documentation :**
- [ ] CHANGELOG.md mis à jour
- [ ] Code documenté (docstrings)
```

---

**Version projet :** 7.4 FINAL  
**Date documentation :** 11 Février 2026  
**Auteur :** Mec + Claude

**Pour toute question, consulter d'abord :**
1. `docs/ARCHITECTURE.md`
2. `docs/BUGS.md`
3. Code source commenté
