"""
Gestion de la base de données JSON pour le stockage des trades
"""
import json
import logging
import os
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
from config import DB_FILE, INITIAL_CAPITAL

logger = logging.getLogger(__name__)


class TradeDatabase:
    """Gestionnaire de base de données pour les trades"""
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = Path(db_path)
        self._ensure_db_exists()
    
    def _get_default_db(self) -> Dict[str, Any]:
        """Retourne la structure par défaut de la DB"""
        return {
            "balance": INITIAL_CAPITAL,
            "trades": [],
            "current_trade": None,
            "strategies": {
                "sniper_ema": True,
                "sniper_short": True,
                "rsi_bollinger": True
            },
            "trading_mode": "sequential"
        }
    
    def _ensure_db_exists(self) -> None:
        """Crée la DB si elle n'existe pas"""
        if not self.db_path.exists():
            logger.info(f"Création de la base de données : {self.db_path}")
            self.save(self._get_default_db())
    
    def load(self) -> Dict[str, Any]:
        """Charge les données depuis le fichier JSON"""
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
                logger.info("Migration DB : ajout de la stratégie SHORT")
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
            logger.warning("Rechargement de la DB par défaut")
            return self._get_default_db()
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la DB : {e}")
            return self._get_default_db()
    
    def save(self, data: Dict[str, Any]) -> None:
        """
        Sauvegarde les données dans le fichier JSON.
        
        CORRECTION v8.3 : Écriture atomique via fichier temporaire + rename.
        L'ancienne version écrivait directement dans trades.json : un arrêt brutal
        pendant l'écriture (crash, coupure courant) pouvait corrompre le fichier.
        Avec tmp + rename, soit l'ancien fichier est intact, soit le nouveau l'est.
        """
        try:
            # Écrire dans un fichier temporaire dans le même dossier
            # (même dossier = même filesystem → rename atomique garanti)
            dir_path = self.db_path.parent
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=dir_path,
                suffix='.tmp',
                delete=False
            ) as tmp_file:
                json.dump(data, tmp_file, indent=4, ensure_ascii=False)
                tmp_path = tmp_file.name
            
            # Rename atomique : remplace trades.json en une opération indivisible
            os.replace(tmp_path, self.db_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la DB : {e}")
            # Nettoyage du fichier temporaire si le rename a échoué
            try:
                if 'tmp_path' in locals():
                    os.unlink(tmp_path)
            except Exception:
                pass
            raise
    
    def get_balance(self) -> float:
        """Retourne le balance actuel"""
        data = self.load()
        return data.get('balance', INITIAL_CAPITAL)
    
    def update_balance(self, new_balance: float) -> None:
        """Met à jour le balance"""
        data = self.load()
        data['balance'] = new_balance
        self.save(data)
    
    def add_trade(self, trade: Dict[str, Any]) -> None:
        """Ajoute un trade à l'historique"""
        data = self.load()
        data['trades'].append(trade)
        self.save(data)
        logger.info(f"Trade ajouté : {trade['result']} - P&L: {trade.get('profit_loss', 0):.2f}$")
    
    def get_current_trade(self) -> Optional[Dict[str, Any]]:
        """Retourne le trade en cours"""
        data = self.load()
        return data.get('current_trade')
    
    def set_current_trade(self, trade: Optional[Dict[str, Any]]) -> None:
        """Définit le trade en cours"""
        data = self.load()
        data['current_trade'] = trade
        self.save(data)
    
    def is_strategy_active(self, strategy_name: str) -> bool:
        """Vérifie si une stratégie est active"""
        data = self.load()
        return data.get('strategies', {}).get(strategy_name, False)
    
    def toggle_strategy(self, strategy_name: str) -> bool:
        """Active/désactive une stratégie et retourne le nouvel état"""
        data = self.load()
        current_state = data['strategies'].get(strategy_name, False)
        data['strategies'][strategy_name] = not current_state
        self.save(data)
        new_state = not current_state
        logger.info(f"Stratégie '{strategy_name}' : {'ACTIVÉE' if new_state else 'DÉSACTIVÉE'}")
        return new_state


# Instance globale
db = TradeDatabase()
