"""
Moteur de backtest pour la stratégie RSI Bollinger 15min
"""
import ccxt
import pandas as pd
import asyncio
import logging
from typing import Dict, Any
from strategies.rsi_bollinger_15m import RSIBollingerStrategy
from config import TIMEFRAME, BACKTEST_INITIAL_CAPITAL

logger = logging.getLogger(__name__)


class BacktestRSIEngine:
    """Moteur de simulation de backtest pour RSI Bollinger"""
    
    def __init__(self):
        self.exchange = ccxt.binance()
        self.initial_capital = BACKTEST_INITIAL_CAPITAL
    
    async def fetch_historical_data(self, candles: int) -> pd.DataFrame:
        """Télécharge les données historiques (bougies 15min)"""
        logger.info(f"📥 Téléchargement de {candles} bougies 15min BTC/USDT...")
        
        limit = candles
        since = self.exchange.milliseconds() - (limit * 15 * 60 * 1000)
        all_ohlcv = []
        
        max_iterations = (candles // 1000) + 2
        iteration = 0
        
        while len(all_ohlcv) < limit and iteration < max_iterations:
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    'BTC/USDT',
                    '15m',
                    limit=1000,
                    since=since
                )
                
                if len(ohlcv) == 0:
                    break
                
                since = ohlcv[-1][0] + 1
                all_ohlcv += ohlcv
                await asyncio.sleep(0.05)
                iteration += 1
                
            except Exception as e:
                logger.error(f"Erreur téléchargement : {e}")
                break
        
        if not all_ohlcv:
            raise ValueError("Aucune donnée téléchargée")
        
        df = pd.DataFrame(
            all_ohlcv,
            columns=['time', 'open', 'high', 'low', 'close', 'volume']
        )
        
        logger.info(f"✅ {len(df)} bougies téléchargées")
        return df
    
    def run_simulation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Exécute la simulation de backtest"""
        df = RSIBollingerStrategy.add_indicators(df)
        
        balance = self.initial_capital
        trades = 0
        wins = 0
        
        i = 30  # Commencer après indicateurs
        
        while i < len(df) - 1:
            current_candle = df.iloc[i]
            previous_candle = df.iloc[i - 1]
            
            signal = RSIBollingerStrategy.check_signal(current_candle, previous_candle)
            
            if signal:
                entry_price = current_candle['close']
                levels = RSIBollingerStrategy.calculate_levels(entry_price, signal)
                
                outcome = None
                exit_index = i
                
                for j in range(i + 1, len(df)):
                    future_candle = df.iloc[j]
                    
                    if future_candle['low'] <= levels['stop_loss']:
                        outcome = "LOSS"
                        pnl = -(balance * RSIBollingerStrategy.RISK_PER_TRADE)
                        balance += pnl
                        exit_index = j
                        break
                    elif future_candle['high'] >= levels['take_profit']:
                        outcome = "WIN"
                        pnl = balance * (RSIBollingerStrategy.RISK_PER_TRADE * RSIBollingerStrategy.REWARD_RATIO)
                        balance += pnl
                        exit_index = j
                        break
                
                if outcome:
                    trades += 1
                    if outcome == "WIN":
                        wins += 1
                    i = exit_index
            
            i += 1
        
        pnl_dollars = balance - self.initial_capital
        pnl_percent = (pnl_dollars / self.initial_capital) * 100
        win_rate = (wins / trades * 100) if trades > 0 else 0
        
        return {
            'final_balance': balance,
            'pnl_dollars': pnl_dollars,
            'pnl_percent': pnl_percent,
            'total_trades': trades,
            'wins': wins,
            'losses': trades - wins,
            'win_rate': win_rate
        }
    
    async def run_backtest(self, candles: int, progress_callback=None) -> str:
        """Lance un backtest complet"""
        try:
            if progress_callback:
                await progress_callback(
                    f"⏳ **Téléchargement de {candles} bougies 15min...**"
                )
            
            df = await self.fetch_historical_data(candles)
            
            if progress_callback:
                await progress_callback(
                    f"⚙️ **Simulation RSI Bollinger sur {len(df)} bougies...**"
                )
            
            results = self.run_simulation(df)
            
            report = self._format_report(candles, results)
            
            logger.info(f"Backtest RSI terminé : {results['total_trades']} trades, WR: {results['win_rate']:.1f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur backtest RSI : {e}", exc_info=True)
            return f"❌ **Erreur Backtest RSI**\n\n```text\n{str(e)}\n```"
    
    def _format_report(self, candles: int, results: Dict[str, Any]) -> str:
        """Formate les résultats"""
        hours = (candles * 15) // 60
        return (
            f"🧪 **RÉSULTAT BACKTEST RSI BOLLINGER ({hours}H / {candles} bougies)**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"🏦 **Départ :** {self.initial_capital:.2f} $\n"
            f"💰 **Final :** {results['final_balance']:.2f} $\n"
            f"📈 **P&L :** {results['pnl_dollars']:+.2f} $ ({results['pnl_percent']:+.1f}%)\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"🎲 **Trades :** {results['wins']} Wins / {results['total_trades']} Total\n"
            f"🏆 **Win Rate :** {results['win_rate']:.1f}%\n"
            "⏰ **Timeframe :** 15min\n"
            "📊 **Indicateurs :** RSI(14) + BB(25,2)"
        )
