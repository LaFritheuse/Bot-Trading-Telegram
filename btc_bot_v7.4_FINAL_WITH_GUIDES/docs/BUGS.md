# 🐛 BUGS - Historique et résolution

Documentation de tous les bugs rencontrés et corrigés.

---

## ✅ BUGS CORRIGÉS (v7.4)

### 1. 🔴 BUG CRITIQUE - Incohérence backtest solo vs multi

**Date découverte :** 11 Février 2026  
**Sévérité :** CRITIQUE  
**Status :** ✅ CORRIGÉ (v7.4)

#### Symptômes
```
Backtest solo LONG (720h) : 15 trades, 60% WR
Backtest multi LONG (720h) : 12 trades, 75% WR  ← Incohérent !
```

#### Cause racine
```python
# backtest.py (CORRECT)
if future_candle['low'] <= levels['stop_loss']:  # Vérifie LOW
    outcome = "LOSS"

# backtest_multi.py v7.3 (INCORRECT)
exit_result = StrategyClass.check_exit(future_candle['close'], trade)  # Vérifie CLOSE
```

**Pourquoi c'est un problème :**
```
Bougie :
  Open  : 100
  High  : 105  ← TP touché !
  Low   : 98   ← SL touché !
  Close : 102

backtest.py → Détecte SL (check LOW)
backtest_multi.py v7.3 → Rate SL (check CLOSE)
→ Résultats différents
```

#### Solution
Remplacer `check_exit(close)` par vérification directe `high`/`low` :

```python
# backtest_multi.py v7.4 (CORRIGÉ)
if future_candle['low'] <= temp_trade['stop_loss']:
    outcome = "LOSS"
    exit_index = j
    break
elif future_candle['high'] >= temp_trade['take_profit']:
    outcome = "WIN"
    exit_index = j
    break
```

#### Fichiers modifiés
- `backtest_multi.py` ligne 228 (mode séquentiel)
- `backtest_multi.py` ligne 228 (mode parallèle)

#### Impact
- Résultats maintenant cohérents entre tous les moteurs ✅
- Win Rate plus réaliste (détecte SL correctement) ✅

---

### 2. 🎨 Emojis cassés dans l'interface

**Date découverte :** 10 Février 2026  
**Sévérité :** MOYENNE (visuel)  
**Status :** ✅ CORRIGÉ (v7.4)

#### Symptômes
```
Interface affiche :
ðŸŸ¢ au lieu de 🟢
â„¹ï¸ au lieu de ℹ️
ðŸ'° au lieu de 💰
```

#### Cause racine
- Fichiers uploadés initialement avec encoding UTF-8 corrompu
- Bytes d'emojis mal interprétés

**Exemple corruption :**
```python
# Bytes corrompus
b'\xc3\xb0\xc5\xb8\xc5\x93\xe2\x80\xa2'  # ðŸŸ¢

# Bytes corrects
'🟢'.encode('utf-8')  # b'\xf0\x9f\x9f\xa2'
```

#### Solution
Script Python de remplacement bytes corrompus → emojis corrects :

```python
emoji_map = {
    b'\xc3\xb0\xc5\xb8\xc5\x93\xe2\x80\xa2': '🟢'.encode('utf-8'),
    b'\xc3\xa2\xc5\xa1\xc2\xb9\xc3\xaf\xc2\xb8\xc2\x8f': 'ℹ️'.encode('utf-8'),
    # ... etc
}

with open(file, 'rb') as f:
    content = f.read()
for old, new in emoji_map.items():
    content = content.replace(old, new)
with open(file, 'wb') as f:
    f.write(content)
```

#### Fichiers corrigés
- `ui/keyboards.py`
- `ui/messages.py`
- `backtest.py`
- `backtest_short.py`
- `backtest_multi.py`
- `backtest_rsi.py`

#### Validation
- Test visuel dans Telegram ✅
- Tous emojis affichent correctement ✅

---

### 3. ❌ AttributeError: '_handle_strategy_rsi_info'

**Date découverte :** 11 Février 2026  
**Sévérité :** HAUTE (crash)  
**Status :** ✅ CORRIGÉ (v7.4)

#### Symptômes
```
Traceback (most recent call last):
  File "handlers/callbacks.py", line 92
    'info_rsi': self._handle_strategy_rsi_info,
AttributeError: 'CallbackHandler' object has no attribute '_handle_strategy_rsi_info'
```

#### Cause racine
- Handlers RSI déclarés dans routeur (ligne 92) mais fonctions non créées
- Oubli lors de l'intégration RSI

**Handlers manquants :**
```python
1. _handle_toggle_rsi
2. _handle_strategy_rsi_info
3. _handle_backtest_duration_rsi_menu
4. _handle_custom_backtest_rsi_input
5. _handle_run_backtest_rsi
6. _handle_btm_toggle_rsi
```

#### Solution
Création des 6 handlers manquants dans `callbacks.py` :

```python
async def _handle_toggle_rsi(self, query, context):
    """Active/désactive la stratégie RSI Bollinger"""
    db.toggle_strategy('rsi_bollinger')
    await self._handle_strategies_menu(query, context)

async def _handle_strategy_rsi_info(self, query, context):
    """Affiche les informations de la stratégie RSI Bollinger"""
    await query.edit_message_text(
        text=get_strategy_rsi_info_text(),
        reply_markup=get_info_rsi_keyboard(),
        parse_mode='Markdown'
    )

# ... etc (4 autres handlers)
```

#### Validation
- 27 handlers déclarés = 27 handlers définis ✅
- Compilation Python OK ✅
- Tous boutons fonctionnels ✅

---

### 4. 🔧 TypeError: get_strategies_keyboard() missing argument

**Date découverte :** 11 Février 2026  
**Sévérité :** HAUTE (crash au clic)  
**Status :** ✅ CORRIGÉ (v7.4)

#### Symptômes
```
Traceback (most recent call last):
  File "handlers/callbacks.py", line 147
    reply_markup=get_strategies_keyboard(sniper_active, sniper_short_active),
TypeError: get_strategies_keyboard() missing 1 required positional argument: 'rsi_active'
```

#### Cause racine
- Fonction modifiée pour 3 paramètres (ajout RSI)
- Appel ancien avec seulement 2 paramètres

**Avant (v7.3) :**
```python
def get_strategies_keyboard(sniper_active: bool, sniper_short_active: bool):
    # ...
```

**Après (v7.4) :**
```python
def get_strategies_keyboard(sniper_active: bool, sniper_short_active: bool, rsi_active: bool):
    # ...
```

**Appel non mis à jour :**
```python
# callbacks.py ligne 147 (v7.3)
reply_markup=get_strategies_keyboard(sniper_active, sniper_short_active)  # ❌ Manque rsi_active
```

#### Solution
Ajouter récupération et passage du 3ème paramètre :

```python
# callbacks.py ligne 147 (v7.4 CORRIGÉ)
rsi_active = db_data.get('strategies', {}).get('rsi_bollinger', True)
reply_markup=get_strategies_keyboard(sniper_active, sniper_short_active, rsi_active)
```

#### Validation
- Menu stratégies affiche 3 boutons ✅
- Toggle RSI fonctionne ✅

---

## ⚠️ BUGS CONNUS (non résolus)

### Aucun bug connu actuellement (v7.4)

Tous les bugs identifiés ont été corrigés dans la version 7.4.

---

## 🔍 Comment tester un bug

### 1. Reproduire le bug
```bash
# Lancer le bot
python3 main.py

# Suivre les étapes qui causent le bug
# Noter la trace d'erreur complète
```

### 2. Identifier la cause
```python
# Ajouter logs de debug
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Variable X : {x}")
logger.debug(f"Type : {type(x)}")
logger.debug(f"Valeur : {repr(x)}")
```

### 3. Créer un test
```python
# test_bug.py
def test_reproduction():
    # Setup
    data = {...}
    
    # Action qui cause le bug
    result = fonction_buggée(data)
    
    # Assert attendu
    assert result == valeur_attendue
```

### 4. Corriger
- Modifier le code source
- Re-tester
- Valider comportement correct

### 5. Documenter
- Ajouter entrée dans BUGS.md
- Mettre à jour CHANGELOG.md
- Commit avec message : "fix: description du bug"

---

## 📋 Template rapport de bug

```markdown
### Titre court du bug

**Date :** JJ/MM/AAAA
**Sévérité :** CRITIQUE / HAUTE / MOYENNE / BASSE
**Status :** ❌ ACTIF / ✅ CORRIGÉ / 🔄 EN COURS

#### Symptômes
Description du comportement observé

#### Cause racine
Explication technique de la cause

#### Solution
Comment le bug a été corrigé

#### Fichiers modifiés
- fichier1.py
- fichier2.py

#### Validation
- [ ] Tests passent
- [ ] Comportement correct
```

---

## 🎯 Prévention bugs futurs

### Bonnes pratiques
1. ✅ Tests unitaires pour fonctions critiques
2. ✅ Validation types (type hints)
3. ✅ Logs détaillés (debug mode)
4. ✅ Try/except autour API calls
5. ✅ Vérification arguments avant appels

### Checklist avant commit
- [ ] Code compile sans erreurs
- [ ] Tous handlers déclarés = définis
- [ ] Tests manuels dans Telegram
- [ ] Logs n'affichent pas d'erreurs
- [ ] Documentation à jour

---

**Version :** 7.4  
**Dernière mise à jour :** 11 Février 2026
