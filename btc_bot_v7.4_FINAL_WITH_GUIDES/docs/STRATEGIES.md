# 📊 DÉTAILS DES STRATÉGIES DE TRADING

## Vue d'ensemble

Le bot intègre **3 stratégies de trading** automatisées avec gestion du risque identique (SL: 1.5%, TP: 4.5%).

---

## 1. 🎯 SNIPER V11 LONG (1H)

**Fichier :** `strategies/sniper_v11.py`  
**Timeframe :** 1 heure  
**Direction :** LONG (achat)

### Indicateurs
```python
EMA 200  : Tendance long terme
Volume   : Confirmation momentum
SMA Vol 20 : Moyenne volume 20 périodes
```

### Conditions d'entrée
```python
✅ 1. Prix > EMA 200 (tendance haussière)
✅ 2. Prix PRÉCÉDENT < EMA 200 (breakout)
✅ 3. Volume > 1.5x moyenne volume
```

### Logique
Signal de **breakout haussier** avec confirmation volume forte.  
→ Le prix casse la résistance EMA 200 avec volume exceptionnel.

### Gestion de position
```python
Entry   : Prix de clôture bougie signal
SL      : Entry - 1.5%
TP      : Entry + 4.5%
Ratio   : 1:3
```

### Performance typique
- **Win Rate attendu :** 50-60%
- **Ratio risque/récompense :** 1:3
- **Nombre trades :** Variable (dépend volatilité)

### Code clé
```python
@staticmethod
def check_signal(current_candle, previous_candle) -> bool:
    # Prix actuel au-dessus EMA 200
    above_ema = current_candle['close'] > current_candle['ema_200']
    
    # Prix précédent en-dessous EMA 200 (breakout)
    was_below = previous_candle['close'] < previous_candle['ema_200']
    
    # Volume > 1.5x moyenne
    volume_surge = current_candle['volume'] > (current_candle['volume_sma'] * 1.5)
    
    return above_ema and was_below and volume_surge
```

---

## 2. 📉 SNIPER V11 SHORT (1H)

**Fichier :** `strategies/sniper_short_v11.py`  
**Timeframe :** 1 heure  
**Direction :** SHORT (vente)

### Indicateurs
Identiques à Sniper LONG (EMA 200, Volume, SMA Vol 20)

### Conditions d'entrée
```python
✅ 1. Prix < EMA 200 (tendance baissière)
✅ 2. Prix PRÉCÉDENT > EMA 200 (breakout inverse)
✅ 3. Volume > 1.5x moyenne volume
```

### Logique
Signal de **breakout baissier** avec confirmation volume forte.  
→ Le prix casse le support EMA 200 vers le bas avec volume exceptionnel.

### Gestion de position
```python
Entry   : Prix de clôture bougie signal
SL      : Entry + 1.5%  (protection hausse)
TP      : Entry - 4.5%  (profit baisse)
Ratio   : 1:3
```

### Performance typique
- **Win Rate attendu :** 50-60%
- **Moins fréquent** que LONG (marchés crypto + haussiers)

### Code clé
```python
@staticmethod
def check_signal(current_candle, previous_candle) -> bool:
    # Prix actuel en-dessous EMA 200
    below_ema = current_candle['close'] < current_candle['ema_200']
    
    # Prix précédent au-dessus EMA 200 (breakout inverse)
    was_above = previous_candle['close'] > previous_candle['ema_200']
    
    # Volume > 1.5x moyenne
    volume_surge = current_candle['volume'] > (current_candle['volume_sma'] * 1.5)
    
    return below_ema and was_above and volume_surge
```

---

## 3. 📊 RSI BOLLINGER 15MIN

**Fichier :** `strategies/rsi_bollinger_15m.py`  
**Timeframe :** 15 minutes (4x plus rapide !)  
**Direction :** LONG et SHORT  
**Win Rate documenté :** 78-82%

### Indicateurs
```python
RSI(14)         : Relative Strength Index
BB Upper(25,2)  : Bande Bollinger supérieure
BB Lower(25,2)  : Bande Bollinger inférieure
Volume SMA(20)  : Moyenne volume
```

### Conditions d'entrée LONG
```python
✅ 1. Prix touche/traverse Bande INFÉRIEURE
✅ 2. RSI < 30 (zone de survente)
✅ 3. Volume > Moyenne volume 20
```

### Conditions d'entrée SHORT
```python
✅ 1. Prix touche/traverse Bande SUPÉRIEURE
✅ 2. RSI > 70 (zone de surachat)
✅ 3. Volume > Moyenne volume 20
```

### Logique
Stratégie de **retournement sur zones extrêmes**.  
→ Identifie conditions de survente/surachat avec Bollinger Bands + RSI.  
→ Entre en position inverse en anticipant rebond/correction.

### Gestion de position
```python
LONG :
  Entry : Prix de clôture bougie signal
  SL    : Entry - 1.5%
  TP    : Entry + 4.5%

SHORT :
  Entry : Prix de clôture bougie signal
  SL    : Entry + 1.5%
  TP    : Entry - 4.5%

Ratio : 1:3
```

### Performance typique
- **Win Rate documenté :** 78-82% (très élevé)
- **Fréquence :** Élevée (15min = 4x plus de signaux que 1h)
- **Risque :** Faux signaux en strong trend (besoin filtre volume)

### Code clé
```python
@staticmethod
def check_signal(current_candle, previous_candle) -> str | None:
    # Signal LONG : survente + touche BB lower
    if (current_candle['low'] <= current_candle['bb_lower'] and 
        current_candle['rsi'] < 30 and
        current_candle['volume'] > current_candle['volume_sma']):
        return "LONG"
    
    # Signal SHORT : surachat + touche BB upper
    elif (current_candle['high'] >= current_candle['bb_upper'] and 
          current_candle['rsi'] > 70 and
          current_candle['volume'] > current_candle['volume_sma']):
        return "SHORT"
    
    return None
```

---

## 🔄 Comparaison des stratégies

| Stratégie | Timeframe | Direction | Win Rate | Fréquence | Philosophie |
|-----------|-----------|-----------|----------|-----------|-------------|
| Sniper LONG | 1H | LONG | 50-60% | Moyenne | Breakout haussier |
| Sniper SHORT | 1H | SHORT | 50-60% | Faible | Breakout baissier |
| RSI Bollinger | 15min | LONG+SHORT | 78-82% | Élevée | Retournement extrêmes |

---

## 📈 Indicateurs techniques utilisés

### EMA (Exponential Moving Average)
```python
Période : 200
Usage   : Filtre tendance (support/résistance dynamique)
Calcul  : pandas_ta.ema(close, length=200)
```

### RSI (Relative Strength Index)
```python
Période : 14
Usage   : Mesure survente/surachat (0-100)
Calcul  : pandas_ta.rsi(close, length=14)
Zones   : 
  - RSI < 30 = Survente (potentiel rebond haussier)
  - RSI > 70 = Surachat (potentiel correction baissière)
```

### Bollinger Bands
```python
Période : 25
Écart   : 2 (2 écarts-types)
Usage   : Bandes dynamiques volatilité
Calcul  : pandas_ta.bbands(close, length=25, std=2)
Composants :
  - BB Upper : Bande supérieure (résistance)
  - BB Lower : Bande inférieure (support)
  - BB Mid   : SMA 25 (ligne médiane)
```

### Volume SMA
```python
Période : 20
Usage   : Filtre confirmation (volume > moyenne = signal fort)
Calcul  : df['volume'].rolling(20).mean()
```

---

## 🎯 Gestion du risque (commune)

### Paramètres fixes
```python
RISK_PER_TRADE = 0.015  # 1.5% du capital par trade
REWARD_RATIO   = 3      # TP = 3x SL
```

### Calcul des niveaux
```python
# Pour LONG
entry = current_candle['close']
sl = entry * (1 - 0.015)      # -1.5%
tp = entry * (1 + 0.045)      # +4.5%

# Pour SHORT
entry = current_candle['close']
sl = entry * (1 + 0.015)      # +1.5%
tp = entry * (1 - 0.045)      # -4.5%
```

### Détection SL/TP dans backtests
**IMPORTANT :** Les backtests utilisent `high` et `low` des bougies (pas juste `close`).

```python
# Mauvaise approche (ancienne v7.3)
if future_candle['close'] <= sl:  # ❌ Rate le SL si touché pendant bougie

# Bonne approche (v7.4+)
if future_candle['low'] <= sl:    # ✅ Détecte SL même si close au-dessus
if future_candle['high'] >= tp:   # ✅ Détecte TP même si close en-dessous
```

---

## 🛠️ Ajouter une nouvelle stratégie

### Template de stratégie
```python
class MaStrategie:
    """Description de ma stratégie"""
    
    # Paramètres
    RISK_PER_TRADE = 0.015
    REWARD_RATIO = 3
    
    @staticmethod
    def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute les indicateurs techniques"""
        import pandas_ta as ta
        
        # Ajouter vos indicateurs
        df['mon_indic'] = ta.mon_indicateur(...)
        
        return df
    
    @staticmethod
    def check_signal(current_candle, previous_candle) -> bool | str:
        """
        Vérifie les conditions d'entrée
        
        Returns:
            bool : True si signal (pour LONG uniquement)
            str : "LONG" ou "SHORT" (pour stratégies bidirectionnelles)
            None/False : Pas de signal
        """
        # Votre logique
        if conditions_long:
            return "LONG"
        elif conditions_short:
            return "SHORT"
        return None
    
    @staticmethod
    def calculate_levels(entry_price: float, signal: str = None) -> dict:
        """
        Calcule Stop Loss et Take Profit
        
        Args:
            entry_price : Prix d'entrée
            signal : "LONG" ou "SHORT" (optionnel)
        """
        if signal == "SHORT":
            sl = entry_price * (1 + MaStrategie.RISK_PER_TRADE)
            tp = entry_price * (1 - (MaStrategie.RISK_PER_TRADE * MaStrategie.REWARD_RATIO))
        else:  # LONG
            sl = entry_price * (1 - MaStrategie.RISK_PER_TRADE)
            tp = entry_price * (1 + (MaStrategie.RISK_PER_TRADE * MaStrategie.REWARD_RATIO))
        
        return {
            'stop_loss': sl,
            'take_profit': tp
        }
```

### Intégration dans le bot
1. Créer fichier `strategies/ma_strategie.py`
2. Ajouter dans `trading.py` :
```python
from strategies.ma_strategie import MaStrategie
self.strategies['ma_strat'] = MaStrategie
```
3. Ajouter dans `database.py` : `"ma_strat": True`
4. Créer `backtest_ma_strat.py`
5. Ajouter UI : keyboards.py + messages.py + callbacks.py

---

**Version :** 7.4  
**Dernière mise à jour :** 11 Février 2026
