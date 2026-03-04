"""
Moteur de trading en temps réel - Version Multi-Stratégies
"""
import ccxt
import pandas as pd
import asyncio
import time
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
    """Moteur de trading en temps réel multi-stratégies"""
    
    def __init__(self):
        self.exchange = ccxt.binance()
        self.symbol = 'BTC/USDT'
        
        # CORRECTION v8.1 : RSI ajouté au mapping (manquant en v8)
        self.strategies = {
            'sniper_ema': SniperV11Strategy,
            'sniper_short': SniperShortV11Strategy,
            'rsi_bollinger': RSIBollingerStrategy
        }
    
    async def check_market(self, context: ContextTypes.DEFAULT_TYPE):
        """
        Vérifie le marché et gère les positions
        
        Cette fonction est appelée périodiquement par le job queue
        
        Args:
            context: Context Telegram
        """
        try:
            scan_start = time.perf_counter()
            current_time = datetime.now().strftime('%H:%M')
            logger.info(f"⚙️ {current_time} - Scan Multi-Stratégies...")
            
            # Charger l'état actuel
            db_data = db.load()
            current_trade = db_data.get('current_trade')

            # Choisir le timeframe selon le trade ouvert (RSI = 15m)
            if current_trade and current_trade.get('strategy') == RSIBollingerStrategy.NAME:
                tf = '15m'
                df = await self._fetch_market_data_15m()
            else:
                tf = TIMEFRAME
                df = await self._fetch_market_data()

            if df is None or len(df) < 3:
                logger.warning(f"Données insuffisantes pour l'analyse (tf={tf})")
                return

            logger.info(f"[CHECK_MARKET] tf={tf} candles={len(df)} last_time={df.iloc[-1]['time']}")

            if current_trade:
                await self._manage_open_position(df, current_trade, context, timeframe=tf)
            else:
                await self._check_for_entry(df, db_data, context)
                
            logger.info(f"[CHECK_MARKET] done tf={tf} in {time.perf_counter() - scan_start:.3f}s")
        except Exception as e:
            logger.error(f"Erreur lors du scan de marché : {e}", exc_info=True)
    
    async def _fetch_market_data(self) -> pd.DataFrame:
        """
        Récupère les données de marché 1h depuis Binance (pour stratégies Sniper)
        
        Returns:
            DataFrame avec les données OHLCV
        """
        try:
            bars = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
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
            logger.error(f"Erreur réseau lors de la récupération des données : {e}")
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"Erreur de l'exchange : {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            return None
    
    async def _fetch_market_data_15m(self) -> pd.DataFrame:
        """
        CORRECTION v8.1 : Récupère les données 15min depuis Binance (pour stratégie RSI).
        Le RSI Bollinger est conçu et backtesté sur 15m — utiliser 1h était une erreur.
        
        Returns:
            DataFrame avec les données OHLCV 15min
        """
        try:
            # 200 bougies 15min suffisent pour les indicateurs RSI/BB
            bars = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
                self.symbol,
                timeframe='15m',
                limit=200
            )
            
            df = pd.DataFrame(
                bars,
                columns=['time', 'open', 'high', 'low', 'close', 'volume']
            )
            
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            
            return df
            
        except ccxt.NetworkError as e:
            logger.error(f"Erreur réseau (15m) : {e}")
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"Erreur exchange (15m) : {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue (15m) : {e}")
            return None
    
    async def _manage_open_position(
        self,
        df: pd.DataFrame,
        trade: dict,
        context: ContextTypes.DEFAULT_TYPE,
        timeframe: str = TIMEFRAME
    ):
        """
        Gère une position ouverte (vérifie SL/TP)

        CORRECTION v8.1 :
        - RSIBollingerStrategy utilisé pour les trades RSI (au lieu de SniperV11)
        - La sélection de classe se fait sur le nom de stratégie stocké dans le trade

        CORRECTION v8.4 :
        - Utilise la dernière bougie COMPLÈTE (df[-2]) pour éviter la bougie en formation
        - Détecte SL/TP via HIGH/LOW (cohérent avec les backtests)

        Args:
            df: DataFrame avec les données de marché
            trade: Trade en cours
            context: Context Telegram
            timeframe: Timeframe utilisé pour ce trade
        """
        if df is None or len(df) < 3:
            logger.warning("Données insuffisantes pour gérer la position")
            return

        candle = df.iloc[-2]  # dernière bougie COMPLÈTE
        candle_time = candle['time']
        close = float(candle['close'])
        high = float(candle['high'])
        low = float(candle['low'])

        # Récupérer le nom de la stratégie du trade
        strategy_name = trade.get('strategy', SniperV11Strategy.NAME)
        direction = trade.get('direction', 'LONG')

        logger.info(
            f"Position {direction} ouverte (tf={timeframe}) : "
            f"t={candle_time} close={close:.2f}$ high={high:.2f}$ low={low:.2f}$ | "
            f"SL: {trade['stop_loss']:.2f}$ | TP: {trade['take_profit']:.2f}$"
        )

        # Sélectionner la bonne classe selon la stratégie du trade
        if strategy_name == RSIBollingerStrategy.NAME:
            StrategyClass = RSIBollingerStrategy
        elif 'SHORT' in strategy_name:
            StrategyClass = SniperShortV11Strategy
        else:
            StrategyClass = SniperV11Strategy

        # Sortie candle-based (high/low)
        exit_result, exit_price = self._check_exit_on_candle(candle, trade)

        if exit_result:
            await self._close_position(trade, exit_result, exit_price, StrategyClass, context)

    @staticmethod
    def _check_exit_on_candle(candle: pd.Series, trade: dict):
        """Détermine si SL/TP a été touché sur une bougie close.

        Hypothèse conservative : si SL et TP sont touchés dans la même bougie, on compte LOSS.

        Returns:
            Tuple (result, exit_price) :
              - ("WIN"|"LOSS", float) si sortie
              - (None, None) sinon
        """
        direction = trade.get('direction', 'LONG')
        sl = float(trade['stop_loss'])
        tp = float(trade['take_profit'])
        high = float(candle['high'])
        low = float(candle['low'])

        if direction == "LONG":
            if low <= sl:
                return "LOSS", sl
            if high >= tp:
                return "WIN", tp
        else:  # SHORT
            if high >= sl:
                return "LOSS", sl
            if low <= tp:
                return "WIN", tp

        return None, None

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
            trade: Trade à fermer
            result: 'WIN' ou 'LOSS'
            exit_price: Prix de sortie
            StrategyClass: Classe de stratégie utilisée
            context: Context Telegram
        """
        # Calculer le P&L
        pnl = StrategyClass.calculate_pnl(result, trade['amount'])
        
        # Mettre à jour le balance
        db_data = db.load()
        new_balance = db_data['balance'] + pnl
        db.update_balance(new_balance)
        
        # Compléter les informations du trade
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
        Vérifie si les conditions d'entrée sont remplies pour les stratégies actives.
        
        CORRECTION v8.1 :
        - La direction du signal est capturée (pas seulement bool) et propagée
        - RSI utilise ses données 15m dédiées (et non le df 1h partagé)
        - Séparation claire entre signal bool (Sniper) et signal str (RSI)
        
        Args:
            df: DataFrame 1h avec les données de marché (pour Sniper)
            db_data: Données de la base de données
            context: Context Telegram
        """
        # Récupérer les stratégies actives
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
        
        # Vérifier chaque stratégie dans l'ordre (mode séquentiel)
        for strat_key, StrategyClass in active_strategies:
            
            # CORRECTION v8.1 : RSI utilise un fetch 15m dédié
            if strat_key == 'rsi_bollinger':
                df_strat = await self._fetch_market_data_15m()
                if df_strat is None or len(df_strat) < 35:
                    logger.warning("Données 15m insuffisantes pour RSI, stratégie ignorée ce cycle")
                    continue
            else:
                df_strat = df
            
            # Ajouter les indicateurs spécifiques à cette stratégie
            df_with_indicators = StrategyClass.add_indicators(df_strat.copy())
            
            last_with_ind = df_with_indicators.iloc[-2]   # Dernière bougie COMPLÈTE
            prev_with_ind = df_with_indicators.iloc[-3]
            
            # CORRECTION v8.1 : capturer la valeur de retour de check_signal
            # Sniper retourne bool, RSI retourne Optional[str] ("LONG"/"SHORT"/None)
            signal = StrategyClass.check_signal(last_with_ind, prev_with_ind)
            
            if signal:
                # Déduire la direction
                if isinstance(signal, str):
                    # RSI Bollinger : retourne directement "LONG" ou "SHORT"
                    direction = signal
                else:
                    # Sniper : retourne True, direction déduite de la clé
                    direction = "SHORT" if strat_key == 'sniper_short' else "LONG"
                
                await self._enter_position(last_with_ind, db_data, StrategyClass, context, direction)
                break  # En mode sequential, on prend le premier signal
    
    async def _enter_position(
        self,
        entry_candle: pd.Series,
        db_data: dict,
        StrategyClass,
        context: ContextTypes.DEFAULT_TYPE,
        direction: str = "LONG"
    ):
        """
        Entre en position.
        
        CORRECTION v8.1 :
        - Accepte et propage le paramètre direction
        - Appelle create_trade_entry avec direction pour RSIBollingerStrategy
        - Les stratégies Sniper gardent leur signature à 3 paramètres
        
        Args:
            entry_candle: Bougie d'entrée
            db_data: Données de la base de données
            StrategyClass: Classe de stratégie à utiliser
            context: Context Telegram
            direction: "LONG" ou "SHORT"
        """
        entry_price = entry_candle['close']
        entry_time = str(entry_candle['time'])
        balance = db_data['balance']
        
        # CORRECTION v8.1 : RSIBollingerStrategy exige direction en 4ème paramètre.
        # Les stratégies Sniper n'ont pas ce paramètre (direction fixe par design).
        if StrategyClass == RSIBollingerStrategy:
            trade = StrategyClass.create_trade_entry(entry_price, balance, entry_time, direction)
        else:
            trade = StrategyClass.create_trade_entry(entry_price, balance, entry_time)
        
        # Sauvegarder
        db.set_current_trade(trade)
        
        logger.info(
            f"📈 ENTRÉE EN POSITION {direction} : {entry_price:.2f}$ | "
            f"SL: {trade['stop_loss']:.2f}$ | TP: {trade['take_profit']:.2f}$"
        )
        
        # Notification
        await context.bot.send_message(
            chat_id=MY_CHAT_ID,
            text=format_trade_entry_notification(entry_price)
        )


# Instance globale
trading_engine = TradingEngine()
