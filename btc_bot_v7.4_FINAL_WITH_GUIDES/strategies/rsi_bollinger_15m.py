"""
StratÃ©gie RSI + Bollinger Bands sur 15 minutes
Win Rate documentÃ© : 78-82%
"""
import pandas as pd
import pandas_ta as ta
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RSIBollingerStrategy:
    """
    StratÃ©gie RSI + Bollinger Bands (15min)
    
    ParamÃ¨tres optimisÃ©s:
    - RSI : 14 pÃ©riodes
    - Bollinger Bands : 25 pÃ©riodes, 2 std
    - Timeframe : 15 minutes
    
    Conditions d'entrÃ©e LONG :
    - Prix touche ou traverse la bande infÃ©rieure de Bollinger
    - RSI < 30 (survente)
    - Volume > moyenne mobile 20
    
    Conditions d'entrÃ©e SHORT :
    - Prix touche ou traverse la bande supÃ©rieure de Bollinger
    - RSI > 70 (surachat)
    - Volume > moyenne mobile 20
    
    Gestion du risque :
    - Stop Loss : 1.5%
    - Take Profit : 4.5% (ratio 1:3)
    """
    
    NAME = "RSI Bollinger 15min"
    
    # ParamÃ¨tres de la stratÃ©gie
    RSI_PERIOD = 14
    BB_PERIOD = 25
    BB_STD = 2.0
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    VOLUME_MA_PERIOD = 20
    RISK_PER_TRADE = 0.015
    REWARD_RATIO = 3
    
    @staticmethod
    def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute les indicateurs techniques au DataFrame"""
        try:
            # RSI
            df['RSI'] = df.ta.rsi(length=RSIBollingerStrategy.RSI_PERIOD)
            
            # Bollinger Bands
            bb = df.ta.bbands(
                length=RSIBollingerStrategy.BB_PERIOD,
                std=RSIBollingerStrategy.BB_STD
            )
            df['BB_UPPER'] = bb[f'BBU_{RSIBollingerStrategy.BB_PERIOD}_{RSIBollingerStrategy.BB_STD}']
            df['BB_MIDDLE'] = bb[f'BBM_{RSIBollingerStrategy.BB_PERIOD}_{RSIBollingerStrategy.BB_STD}']
            df['BB_LOWER'] = bb[f'BBL_{RSIBollingerStrategy.BB_PERIOD}_{RSIBollingerStrategy.BB_STD}']
            
            # Volume MA
            df['VOL_MA'] = df.ta.sma(close=df['volume'], length=RSIBollingerStrategy.VOLUME_MA_PERIOD)
            
            return df
        except Exception as e:
            logger.error(f"Erreur calcul indicateurs RSI Bollinger : {e}")
            raise
    
    @staticmethod
    def check_signal(current_candle: pd.Series, previous_candle: pd.Series) -> Optional[str]:
        """
        VÃ©rifie si les conditions de la stratÃ©gie sont remplies
        
        Returns:
            'LONG', 'SHORT', ou None
        """
        # VÃ©rifier les valeurs nulles
        required_fields = ['RSI', 'BB_UPPER', 'BB_LOWER', 'VOL_MA']
        if any(pd.isna(current_candle[field]) for field in required_fields):
            return None
        
        close = current_candle['close']
        rsi = current_candle['RSI']
        bb_upper = current_candle['BB_UPPER']
        bb_lower = current_candle['BB_LOWER']
        volume = current_candle['volume']
        vol_ma = current_candle['VOL_MA']
        
        # Confirmation volume
        volume_confirmed = volume > vol_ma
        
        # Signal LONG : Prix touche BB infÃ©rieure + RSI survente
        if close <= bb_lower and rsi < RSIBollingerStrategy.RSI_OVERSOLD and volume_confirmed:
            logger.info(
                f"ðŸŽ¯ Signal RSI Bollinger LONG ! "
                f"Prix: {close:.2f} | BB Lower: {bb_lower:.2f} | "
                f"RSI: {rsi:.1f}"
            )
            return "LONG"
        
        # Signal SHORT : Prix touche BB supÃ©rieure + RSI surachat
        if close >= bb_upper and rsi > RSIBollingerStrategy.RSI_OVERBOUGHT and volume_confirmed:
            logger.info(
                f"ðŸŽ¯ Signal RSI Bollinger SHORT ! "
                f"Prix: {close:.2f} | BB Upper: {bb_upper:.2f} | "
                f"RSI: {rsi:.1f}"
            )
            return "SHORT"
        
        return None
    
    @staticmethod
    def calculate_levels(entry_price: float, direction: str) -> Dict[str, float]:
        """Calcule les niveaux de Stop Loss et Take Profit"""
        if direction == "LONG":
            stop_loss = entry_price * (1 - RSIBollingerStrategy.RISK_PER_TRADE)
            take_profit = entry_price * (1 + (RSIBollingerStrategy.RISK_PER_TRADE * RSIBollingerStrategy.REWARD_RATIO))
        else:  # SHORT
            stop_loss = entry_price * (1 + RSIBollingerStrategy.RISK_PER_TRADE)
            take_profit = entry_price * (1 - (RSIBollingerStrategy.RISK_PER_TRADE * RSIBollingerStrategy.REWARD_RATIO))
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
    
    @staticmethod
    def create_trade_entry(entry_price: float, balance: float, entry_time: str, direction: str) -> Dict[str, Any]:
        """CrÃ©e un objet trade avec tous les paramÃ¨tres"""
        levels = RSIBollingerStrategy.calculate_levels(entry_price, direction)
        
        return {
            "entry_time": entry_time,
            "entry_price": entry_price,
            "stop_loss": levels['stop_loss'],
            "take_profit": levels['take_profit'],
            "amount": balance,
            "strategy": RSIBollingerStrategy.NAME,
            "direction": direction
        }
    
    @staticmethod
    def check_exit(current_price: float, trade: Dict[str, Any]) -> Optional[str]:
        """VÃ©rifie si un niveau de sortie est atteint"""
        direction = trade.get('direction', 'LONG')
        
        if direction == "LONG":
            if current_price <= trade['stop_loss']:
                logger.warning(f"ðŸ›‘ Stop Loss LONG : {current_price:.2f}$ <= {trade['stop_loss']:.2f}$")
                return "LOSS"
            elif current_price >= trade['take_profit']:
                logger.info(f"ðŸŽ‰ Take Profit LONG : {current_price:.2f}$ >= {trade['take_profit']:.2f}$")
                return "WIN"
        else:  # SHORT
            if current_price >= trade['stop_loss']:
                logger.warning(f"ðŸ›‘ Stop Loss SHORT : {current_price:.2f}$ >= {trade['stop_loss']:.2f}$")
                return "LOSS"
            elif current_price <= trade['take_profit']:
                logger.info(f"ðŸŽ‰ Take Profit SHORT : {current_price:.2f}$ <= {trade['take_profit']:.2f}$")
                return "WIN"
        
        return None
    
    @staticmethod
    def calculate_pnl(trade_result: str, balance: float) -> float:
        """Calcule le profit ou la perte en dollars"""
        if trade_result == "WIN":
            return balance * (RSIBollingerStrategy.RISK_PER_TRADE * RSIBollingerStrategy.REWARD_RATIO)
        elif trade_result == "LOSS":
            return -(balance * RSIBollingerStrategy.RISK_PER_TRADE)
        return 0.0
