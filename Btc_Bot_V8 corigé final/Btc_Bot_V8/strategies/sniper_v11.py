"""
Stratégie Sniper EMA V11 avec filtre de volume
"""
import pandas as pd
import pandas_ta as ta
import logging
from typing import Dict, Any, Optional
from config import EMA_PERIOD, VOLUME_MA_PERIOD, RISK_PER_TRADE, REWARD_RATIO

logger = logging.getLogger(__name__)


class SniperV11Strategy:
    """
    Stratégie Sniper V11 : Breakout EMA 200 avec confirmation de volume
    
    Conditions d'entrée :
    1. Le prix casse l'EMA 200 à la hausse (bougie précédente sous EMA, bougie actuelle au-dessus)
    2. Le volume de la bougie est supérieur à la moyenne mobile du volume (20 périodes)
    
    Gestion du risque :
    - Stop Loss : -1.5% de l'entrée
    - Take Profit : +4.5% de l'entrée (ratio 1:3)
    """
    
    NAME = "Sniper V11 (Vol)"
    
    @staticmethod
    def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute les indicateurs techniques au DataFrame
        
        Args:
            df: DataFrame avec colonnes OHLCV
            
        Returns:
            DataFrame enrichi avec EMA_200 et VOL_MA_20
        """
        try:
            df['EMA_200'] = df.ta.ema(length=EMA_PERIOD)
            df['VOL_MA_20'] = df.ta.sma(close=df['volume'], length=VOLUME_MA_PERIOD)
            return df
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs : {e}")
            raise
    
    @staticmethod
    def check_signal(current_candle: pd.Series, previous_candle: pd.Series) -> bool:
        """
        Vérifie si les conditions de la stratégie sont remplies
        
        Args:
            current_candle: Bougie actuelle (clôturée)
            previous_candle: Bougie précédente
            
        Returns:
            True si signal d'achat détecté, False sinon
        """
        # Vérification des valeurs nulles
        if pd.isna(current_candle['EMA_200']) or pd.isna(current_candle['VOL_MA_20']):
            return False
        
        # Condition 1 : Breakout EMA 200
        price_was_below = previous_candle['close'] < previous_candle['EMA_200']
        price_now_above = current_candle['close'] > current_candle['EMA_200']
        ema_breakout = price_was_below and price_now_above
        
        # Condition 2 : Volume confirmé
        volume_confirmed = current_candle['volume'] > current_candle['VOL_MA_20']
        
        signal_detected = ema_breakout and volume_confirmed
        
        if signal_detected:
            logger.info(
                f"🎯 Signal Sniper V11 détecté ! "
                f"Prix: {current_candle['close']:.2f}$ | "
                f"EMA: {current_candle['EMA_200']:.2f}$ | "
                f"Vol: {current_candle['volume']:.0f} vs MA: {current_candle['VOL_MA_20']:.0f}"
            )
        
        return signal_detected
    
    @staticmethod
    def calculate_levels(entry_price: float) -> Dict[str, float]:
        """
        Calcule les niveaux de Stop Loss et Take Profit
        
        Args:
            entry_price: Prix d'entrée
            
        Returns:
            Dict avec 'stop_loss' et 'take_profit'
        """
        stop_loss = entry_price * (1 - RISK_PER_TRADE)
        take_profit = entry_price * (1 + (RISK_PER_TRADE * REWARD_RATIO))
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
    
    @staticmethod
    def create_trade_entry(entry_price: float, balance: float, entry_time: str) -> Dict[str, Any]:
        """
        Crée un objet trade avec tous les paramètres
        
        Args:
            entry_price: Prix d'entrée
            balance: Capital disponible
            entry_time: Timestamp de l'entrée
            
        Returns:
            Dict représentant le trade
        """
        levels = SniperV11Strategy.calculate_levels(entry_price)
        
        return {
            "entry_time": entry_time,
            "entry_price": entry_price,
            "stop_loss": levels['stop_loss'],
            "take_profit": levels['take_profit'],
            "amount": balance,
            "strategy": SniperV11Strategy.NAME
        }
    
    @staticmethod
    def check_exit(current_price: float, trade: Dict[str, Any]) -> Optional[str]:
        """
        Vérifie si un niveau de sortie est atteint
        
        Args:
            current_price: Prix actuel
            trade: Trade en cours
            
        Returns:
            'LOSS' si SL touché, 'WIN' si TP touché, None sinon
        """
        if current_price <= trade['stop_loss']:
            logger.warning(f"🛑 Stop Loss atteint : {current_price:.2f}$ <= {trade['stop_loss']:.2f}$")
            return "LOSS"
        elif current_price >= trade['take_profit']:
            logger.info(f"🎉 Take Profit atteint : {current_price:.2f}$ >= {trade['take_profit']:.2f}$")
            return "WIN"
        return None
    
    @staticmethod
    def calculate_pnl(trade_result: str, balance: float) -> float:
        """
        Calcule le profit ou la perte en dollars
        
        Args:
            trade_result: 'WIN' ou 'LOSS'
            balance: Capital au moment du trade
            
        Returns:
            Montant du P&L (positif si WIN, négatif si LOSS)
        """
        if trade_result == "WIN":
            return balance * (RISK_PER_TRADE * REWARD_RATIO)
        elif trade_result == "LOSS":
            return -(balance * RISK_PER_TRADE)
        return 0.0
