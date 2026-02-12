"""
Gestion de la base de donnÃ©es JSON pour le stockage des trades
"""
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from config import DB_FILE, INITIAL_CAPITAL

logger = logging.getLogger(__name__)


class TradeDatabase:
    """Gestionnaire de base de donnÃ©es pour les trades"""
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = Path(db_path)
        self._ensure_db_exists()
    
    def _get_default_db(self) -> Dict[str, Any]:
        """Retourne la structure par dÃ©faut de la DB"""
        return {
            "balance": INITIAL_CAPITAL,
            "trades": [],
            "current_trade": None,
            "strategies": {
                "sniper_ema": True,
                "sniper_short": True,
                "rsi_bollinger": True
            },
            "trading_mode": "sequential"  # "sequential" ou "parallel"
        }
    
    def _ensure_db_exists(self) -> None:
        """CrÃ©e la DB si elle n'existe pas"""
        if not self.db_path.exists():
            logger.info(f"CrÃ©ation de la base de donnÃ©es : {self.db_path}")
            self.save(self._get_default_db())
    
    def load(self) -> Dict[str, Any]:
        """Charge les donnÃ©es depuis le fichier JSON"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Migration : ajoute 'strategies' si manquant
            if "strategies" not in data:
                data["strategies"] = {"sniper_ema": True, "sniper_short": True}
                logger.info("Migration DB : ajout du champ 'strategies'")
                self.save(data)
            
            # Migration : ajoute 'sniper_short' si manquant
            if "sniper_short" not in data["strategies"]:
                data["strategies"]["sniper_short"] = True
                logger.info("Migration DB : ajout de la stratÃ©gie SHORT")
                self.save(data)
            
            # Migration : ajoute 'trading_mode' si manquant
            if "trading_mode" not in data:
                data["trading_mode"] = "sequential"
                logger.info("Migration DB : ajout du mode de trading")
                self.save(data)
            
            # Migration : ajoute 'rsi_bollinger' si manquant
            if "rsi_bollinger" not in data["strategies"]:
                data["strategies"]["rsi_bollinger"] = True
                logger.info("Migration DB : ajout de la stratégie RSI Bollinger")
                self.save(data)
            
            return data
        
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON : {e}")
            logger.warning("Rechargement de la DB par dÃ©faut")
            return self._get_default_db()
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la DB : {e}")
            return self._get_default_db()
    
    def save(self, data: Dict[str, Any]) -> None:
        """Sauvegarde les donnÃ©es dans le fichier JSON"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la DB : {e}")
            raise
    
    def get_balance(self) -> float:
        """Retourne le balance actuel"""
        data = self.load()
        return data.get('balance', INITIAL_CAPITAL)
    
    def update_balance(self, new_balance: float) -> None:
        """Met Ã  jour le balance"""
        data = self.load()
        data['balance'] = new_balance
        self.save(data)
    
    def add_trade(self, trade: Dict[str, Any]) -> None:
        """Ajoute un trade Ã  l'historique"""
        data = self.load()
        data['trades'].append(trade)
        self.save(data)
        logger.info(f"Trade ajoutÃ© : {trade['result']} - P&L: {trade.get('profit_loss', 0):.2f}$")
    
    def get_current_trade(self) -> Optional[Dict[str, Any]]:
        """Retourne le trade en cours"""
        data = self.load()
        return data.get('current_trade')
    
    def set_current_trade(self, trade: Optional[Dict[str, Any]]) -> None:
        """DÃ©finit le trade en cours"""
        data = self.load()
        data['current_trade'] = trade
        self.save(data)
    
    def is_strategy_active(self, strategy_name: str) -> bool:
        """VÃ©rifie si une stratÃ©gie est active"""
        data = self.load()
        return data.get('strategies', {}).get(strategy_name, False)
    
    def toggle_strategy(self, strategy_name: str) -> bool:
        """Active/dÃ©sactive une stratÃ©gie et retourne le nouvel Ã©tat"""
        data = self.load()
        current_state = data['strategies'].get(strategy_name, False)
        data['strategies'][strategy_name] = not current_state
        self.save(data)
        new_state = not current_state
        logger.info(f"StratÃ©gie '{strategy_name}' : {'ACTIVÃ‰E' if new_state else 'DÃ‰SACTIVÃ‰E'}")
        return new_state


# Instance globale
db = TradeDatabase()
