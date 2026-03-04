# 🎯 BTC Trader Bot V8

Bot de trading Bitcoin automatisé avec interface Telegram.

## 📋 Caractéristiques

- **3 stratégies** :
  - **Sniper LONG (1h)**
  - **Sniper SHORT (1h)**
  - **RSI Bollinger (15m)**
- **Interface Telegram** : Contrôle complet du bot via Telegram
- **Backtests intégrés** : LONG / SHORT / RSI sur données historiques
- **Gestion du risque** : paramètres par stratégie (voir `config.py` + fichiers de stratégie)
- **Logs détaillés** : Suivi complet de toutes les opérations

### 🔬 Recherche (hors bot)

Le dossier `research/` permet de tester des stratégies rapidement sans toucher au bot.
Voir `docs/RESEARCH.md`.

## 🚀 Installation

### 1. Prérequis

- Python 3.8 ou supérieur
- Un compte Telegram
- Un bot Telegram (créé via @BotFather)

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

Ou avec `py` sur Windows :

```bash
py -m pip install -r requirements.txt
```

### 3. Configuration

1. **Créer le fichier `.env`** :
   ```bash
   cp .env.example .env
   ```

2. **Éditer le fichier `.env`** avec vos informations :
   ```
   TELEGRAM_TOKEN=votre_token_ici
   MY_CHAT_ID=votre_chat_id_ici
   ```

   📌 **Comment obtenir ces informations ?**
   
   - **TELEGRAM_TOKEN** : Créez un bot via [@BotFather](https://t.me/botfather) sur Telegram
   - **MY_CHAT_ID** : Utilisez [@userinfobot](https://t.me/userinfobot) pour obtenir votre ID

## ▶️ Lancement

```bash
python main.py
```

Ou sur Windows :

```bash
py main.py
```

Le bot démarrera et enverra un message sur Telegram avec le dashboard.

## 📱 Utilisation

### Interface Telegram

Une fois le bot démarré, vous recevrez un message avec le dashboard principal :

- **📉 Stratégies & Plans** : Activer/désactiver les stratégies
- **📊 Performance & Historique** : Voir vos résultats
- **♻️ Actualiser** : Rafraîchir le dashboard
- **🛑 Éteindre le Bot** : Arrêter le bot

### Backtest

1. Menu Stratégies → ℹ️ Info → 🧪 Lancer Backtest
2. Choisir une durée (ou un nombre de bougies pour RSI)
3. Le bot simulera la stratégie sur les données historiques

## 📁 Structure du projet

```
btc_bot/
├── main.py              # Point d'entrée
├── config.py            # Configuration
├── database.py          # Gestion base de données
├── backtest.py          # Backtest LONG
├── backtest_short.py    # Backtest SHORT
├── backtest_rsi.py      # Backtest RSI
├── trading.py           # Logique de trading live
├── strategies/
│   ├── sniper_v11.py         # Stratégie Sniper LONG (1h)
│   ├── sniper_short_v11.py   # Stratégie Sniper SHORT (1h)
│   └── rsi_bollinger_15m.py  # Stratégie RSI Bollinger (15m)
├── ui/
│   ├── keyboards.py     # Keyboards Telegram
│   └── messages.py      # Messages formatés
├── handlers/
│   ├── commands.py      # Handlers de commandes
│   └── callbacks.py     # Handlers de callbacks
├── .env                 # Variables d'environnement (à créer)
├── .env.example         # Exemple de configuration
├── requirements.txt     # Dépendances Python
├── research/            # Backtests & recherche hors-bot (non-production)
└── trades.json          # Base de données (créée auto)
```

## ⚙️ Configuration avancée

Vous pouvez modifier les paramètres dans `config.py` :

- `TIMEFRAME` : Unité de temps (1h par défaut)
- `RISK_PER_TRADE` : Risque par trade (1.5% par défaut)
- `REWARD_RATIO` : Ratio risque/récompense (3 par défaut)
- `INITIAL_CAPITAL` : Capital initial (1000$ par défaut)
- `EMA_PERIOD` : Période de l'EMA (200 par défaut)
- `VOLUME_MA_PERIOD` : Période de la MA du volume (20 par défaut)

## 🔒 Sécurité

**⚠️ NE JAMAIS** :
- Partager votre fichier `.env`
- Commit le fichier `.env` sur Git
- Partager votre TOKEN Telegram

Le fichier `.env` est déjà dans `.gitignore`.

## 📊 Stratégie Sniper V11

### Conditions d'entrée

1. **Breakout EMA 200** : Le prix doit casser l'EMA 200 à la hausse
2. **Confirmation Volume** : Le volume de la bougie doit être supérieur à la moyenne mobile (20 périodes)

### Gestion du risque

- **Stop Loss** : -1.5% du prix d'entrée
- **Take Profit** : +4.5% du prix d'entrée (ratio 1:3)

### Philosophie

Sécurité maximale avec filtrage des mouvements faibles via le volume.

## 📝 Logs

Les logs sont enregistrés dans :
- **Console** : Logs en temps réel
- **bot.log** : Fichier de logs persistant

## 🐛 Dépannage

### Le bot ne démarre pas

```
ValueError: TELEGRAM_TOKEN manquant
```
→ Vérifiez que vous avez bien créé le fichier `.env` avec votre token

### Erreur de connexion à Binance

```
ccxt.NetworkError
```
→ Vérifiez votre connexion Internet ou réessayez plus tard

### Le bot ne répond pas sur Telegram

→ Vérifiez que le `MY_CHAT_ID` est correct

## ⚠️ Avertissement

Ce bot est fourni à titre éducatif. Le trading de cryptomonnaies comporte des risques importants. Ne tradez jamais plus que ce que vous pouvez vous permettre de perdre.

## 📄 Licence

Code libre d'utilisation pour un usage personnel.

## 🤝 Support

Pour toute question, consultez les logs dans `bot.log`.
