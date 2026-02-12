# 📦 Installation BTC Trader Bot V7.4

## 🚀 Installation Rapide

### 1. Prérequis
- Python 3.8+
- Un bot Telegram (créé via @BotFather)
- Votre Chat ID Telegram (obtenir via @userinfobot)

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration

1. Copiez `.env.example` vers `.env`
2. Éditez `.env` avec vos credentials :

```bash
TELEGRAM_TOKEN=votre_token_du_botfather
MY_CHAT_ID=votre_chat_id
```

### 4. Lancement

**Linux/Mac :**
```bash
chmod +x run.sh
./run.sh
```

**Windows :**
```bash
run.bat
```

**Manuel :**
```bash
python3 main.py
```

## 📊 Stratégies Incluses

1. **Sniper V11 LONG (1H)** - Breakout EMA 200 + Volume
2. **Sniper V11 SHORT (1H)** - Breakout inverse + Volume  
3. **RSI Bollinger (15min)** - Win Rate 78-82% documenté

## 🎯 Fonctionnalités

- ✅ Trading automatique en temps réel
- ✅ Interface Telegram complète
- ✅ Backtest individuel par stratégie
- ✅ Backtest multi-stratégies (séquentiel/parallèle)
- ✅ Gestion du risque 1.5% / Ratio 3:1
- ✅ Logs détaillés

## 📝 Notes

- Le fichier `trades.json` sera créé automatiquement
- Les backtests utilisent les données réelles de Binance
- Mode papier trading par défaut (simulation)

Consultez `README.md` pour plus de détails.
