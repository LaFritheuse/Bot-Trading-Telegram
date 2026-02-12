"""
Moteur de trading en temps rÃ©el - Version Multi-StratÃ©gies
"""
import ccxt
import pandas as pd
import logging
from datetime import datetime
from telegram.ext import ContextTypes

from database import db
from strategies.sniper_v11 import SniperV11Strategy
from strategies.sniper_short_v11 import SniperShortV11Strategy
from strategies.rsi_bollinger_15m import RSIBollingerStrategy
from config import TIMEFRAME, MY_CHAT_ID
from ui.messages import (
    format_trade_entry_notification,
    format_stop_loss_notification,
    format_take_profit_notification
)

logger = logging.getLogger(__name__)


class TradingEngine:
    """Moteur de trading en temps rÃ©el multi-stratÃ©gies"""
    
    def __init__(self):
        self.exchange = ccxt.binance()
        self.symbol = 'BTC/USDT'
        
        # Mapping des stratÃ©gies
        self.strategies = {
            'sniper_ema': SniperV11Strategy,
            'sniper_short': SniperShortV11Strategy
        }
    
    async def check_market(self, context: ContextTypes.DEFAULT_TYPE):
        """
        VÃ©rifie le marchÃ© et gÃ¨re les positions
        
        Cette fonction est appelÃ©e pÃ©riodiquement par le job queue
        
        Args:
            context: Context Telegram
        """
        try:
            current_time = datetime.now().strftime('%H:%M')
            logger.info(f"âš™ï¸ {current_time} - Scan Multi-StratÃ©gies...")
            
            # Charger l'Ã©tat actuel
            db_data = db.load()
            
            # RÃ©cupÃ©rer les donnÃ©es du marchÃ©
            df = await self._fetch_market_data()
            
            if df is None or len(df) < 2:
                logger.warning("DonnÃ©es insuffisantes pour l'analyse")
                return
            
            # VÃ©rifier si on a une position ouverte
            current_trade = db_data.get('current_trade')
            
            if current_trade:
                await self._manage_open_position(df, current_trade, context)
            else:
                await self._check_for_entry(df, db_data, context)
                
        except Exception as e:
            logger.error(f"Erreur lors du scan de marchÃ© : {e}", exc_info=True)
    
    async def _fetch_market_data(self) -> pd.DataFrame:
        """
        RÃ©cupÃ¨re les donnÃ©es de marchÃ© depuis Binance
        
        Returns:
            DataFrame avec les donnÃ©es OHLCV et indicateurs
        """
        try:
            # RÃ©cupÃ©rer 300 bougies pour avoir assez de donnÃ©es pour l'EMA 200
            bars = self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe=TIMEFRAME,
                limit=300
            )
            
            df = pd.DataFrame(
                bars,
                columns=['time', 'open', 'high', 'low', 'close', 'volume']
            )
            
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            
            return df
            
        except ccxt.NetworkError as e:
            logger.error(f"Erreur rÃ©seau lors de la rÃ©cupÃ©ration des donnÃ©es : {e}")
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"Erreur de l'exchange : {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            return None
    
    async def _manage_open_position(
        self,
        df: pd.DataFrame,
        trade: dict,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        GÃ¨re une position ouverte (vÃ©rifie SL/TP)
        
        Args:
            df: DataFrame avec les donnÃ©es de marchÃ©
            trade: Trade en cours
            context: Context Telegram
        """
        # Utiliser le prix actuel (derniÃ¨re bougie clÃ´turÃ©e)
        current_price = df.iloc[-1]['close']
        
        # RÃ©cupÃ©rer la stratÃ©gie du trade
        strategy_name = trade.get('strategy', 'Sniper V11 (Vol)')
        direction = trade.get('direction', 'LONG')
        
        logger.info(
            f"Position {direction} ouverte : Prix actuel {current_price:.2f}$ | "
            f"SL: {trade['stop_loss']:.2f}$ | TP: {trade['take_profit']:.2f}$"
        )
        
        # DÃ©terminer quelle classe utiliser pour check_exit
        if 'SHORT' in strategy_name:
            StrategyClass = SniperShortV11Strategy
        else:
            StrategyClass = SniperV11Strategy
        
        # VÃ©rifier la sortie
        exit_result = StrategyClass.check_exit(current_price, trade)
        
        if exit_result:
            await self._close_position(trade, exit_result, current_price, StrategyClass, context)
    
    async def _close_position(
        self,
        trade: dict,
        result: str,
        exit_price: float,
        StrategyClass,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Ferme une position
        
        Args:
            trade: Trade Ã  fermer
            result: 'WIN' ou 'LOSS'
            exit_price: Prix de sortie
            StrategyClass: Classe de stratÃ©gie utilisÃ©e
            context: Context Telegram
        """
        # Calculer le P&L
        pnl = StrategyClass.calculate_pnl(result, trade['amount'])
        
        # Mettre Ã  jour le balance
        db_data = db.load()
        new_balance = db_data['balance'] + pnl
        db.update_balance(new_balance)
        
        # ComplÃ©ter les informations du trade
        trade['result'] = result
        trade['exit_price'] = exit_price
        trade['profit_loss'] = pnl
        
        # Archiver le trade
        db.add_trade(trade)
        
        # Effacer le trade en cours
        db.set_current_trade(None)
        
        # Notification
        if result == "LOSS":
            message = format_stop_loss_notification(pnl)
        else:
            message = format_take_profit_notification(pnl)
        
        await context.bot.send_message(
            chat_id=MY_CHAT_ID,
            text=message
        )
    
    async def _check_for_entry(
        self,
        df: pd.DataFrame,
        db_data: dict,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        VÃ©rifie si les conditions d'entrÃ©e sont remplies pour les stratÃ©gies actives
        
        Args:
            df: DataFrame avec les donnÃ©es de marchÃ©
            db_data: DonnÃ©es de la base de donnÃ©es
            context: Context Telegram
        """
        # RÃ©cupÃ©rer les stratÃ©gies actives
        active_strategies = []
        strategies_config = db_data.get('strategies', {})
        
        if strategies_config.get('sniper_ema', False):
            active_strategies.append(('sniper_ema', SniperV11Strategy))
        
        if strategies_config.get('sniper_short', False):
            active_strategies.append(('sniper_short', SniperShortV11Strategy))
        
        if strategies_config.get('rsi_bollinger', False):
            active_strategies.append(('rsi_bollinger', RSIBollingerStrategy))
        
        if not active_strategies:
            return
        
        # Mode de trading : sequential ou parallel
        # Pour l'instant, on gÃ¨re seulement sequential (1 trade Ã  la fois)
        # Le mode parallel nÃ©cessiterait une architecture diffÃ©rente avec plusieurs trades simultanÃ©s
        
        # Analyser les deux derniÃ¨res bougies clÃ´turÃ©es
        last_candle = df.iloc[-2]  # DerniÃ¨re bougie COMPLÃˆTE
        previous_candle = df.iloc[-3]
        
        # VÃ©rifier chaque stratÃ©gie dans l'ordre
        for strat_key, StrategyClass in active_strategies:
            # Ajouter les indicateurs spÃ©cifiques Ã  cette stratÃ©gie
            df_with_indicators = StrategyClass.add_indicators(df.copy())
            
            last_with_ind = df_with_indicators.iloc[-2]
            prev_with_ind = df_with_indicators.iloc[-3]
            
            # VÃ©rifier le signal
            if StrategyClass.check_signal(last_with_ind, prev_with_ind):
                await self._enter_position(last_with_ind, db_data, StrategyClass, context)
                break  # En mode sequential, on prend le premier signal
    
    async def _enter_position(
        self,
        entry_candle: pd.Series,
        db_data: dict,
        StrategyClass,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Entre en position
        
        Args:
            entry_candle: Bougie d'entrÃ©e
            db_data: DonnÃ©es de la base de donnÃ©es
            StrategyClass: Classe de stratÃ©gie Ã  utiliser
            context: Context Telegram
        """
        entry_price = entry_candle['close']
        entry_time = str(entry_candle['time'])
        balance = db_data['balance']
        
        # CrÃ©er le trade
        trade = StrategyClass.create_trade_entry(
            entry_price,
            balance,
            entry_time
        )
        
        # Sauvegarder
        db.set_current_trade(trade)
        
        direction = trade.get('direction', 'LONG')
        
        logger.info(
            f"ðŸ“ˆ ENTRÃ‰E EN POSITION {direction} : {entry_price:.2f}$ | "
            f"SL: {trade['stop_loss']:.2f}$ | TP: {trade['take_profit']:.2f}$"
        )
        
        # Notification
        await context.bot.send_message(
            chat_id=MY_CHAT_ID,
            text=format_trade_entry_notification(entry_price)
        )


# Instance globale
trading_engine = TradingEngine()
