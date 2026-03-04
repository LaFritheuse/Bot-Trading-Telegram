"""
Configuration centralisée du bot de trading BTC
"""
import os
from pathlib import Path
from typing import Final

# Trouver le fichier .env dans le même dossier que config.py
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / '.env'

# Charger manuellement le .env
if ENV_FILE.exists():
    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# ============================================
# CREDENTIALS (À configurer via .env)
# ============================================
TOKEN: Final[str] = os.getenv('TELEGRAM_TOKEN', '')
MY_CHAT_ID: Final[int] = int(os.getenv('MY_CHAT_ID', '0'))

# ============================================
# PARAMÈTRES DE TRADING
# ============================================
TIMEFRAME: Final[str] = '1h'
RISK_PER_TRADE: Final[float] = 0.015  # 1.5%
REWARD_RATIO: Final[int] = 3  # 4.5% (1.5% * 3)
INITIAL_CAPITAL: Final[float] = 1000.0

# ============================================
# INDICATEURS TECHNIQUES
# ============================================
EMA_PERIOD: Final[int] = 200
VOLUME_MA_PERIOD: Final[int] = 20

# ============================================
# SYSTÈME
# ============================================
DB_FILE: Final[str] = "trades.json"
MARKET_CHECK_INTERVAL: Final[int] = 45  # secondes
MARKET_CHECK_FIRST_RUN: Final[int] = 10  # secondes

# ============================================
# BACKTEST
# ============================================
BACKTEST_INITIAL_CAPITAL: Final[float] = 1000.0
BACKTEST_PRESET_DURATIONS = {
    '1_month': 720,
    '6_months': 4300,
    '1_year': 8760
}

# ============================================
# VALIDATION
# ============================================
def validate_config() -> bool:
    """Valide que la configuration est correcte"""
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN manquant. Verifiez votre fichier .env")
    if MY_CHAT_ID == 0:
        raise ValueError("MY_CHAT_ID manquant. Verifiez votre fichier .env")
    return True