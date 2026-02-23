"""
Moteur de backtest pour la stratégie SHORT uniquement
"""
import ccxt
import pandas as pd
import asyncio
import logging
from typing import Dict, Any
from strategies.sniper_short_v11 import SniperShortV11Strategy
from config import TIMEFRAME, BACKTEST_INITIAL_CAPITAL, RISK_PER_TRADE, REWARD_RATIO

logger = logging.getLogger(__name__)


class BacktestShortEngine:
    """Moteur de simulation de backtest pour stratégie SHORT"""
    
    def __init__(self):
        self.exchange = ccxt.binance()
        self.initial_capital = BACKTEST_INITIAL_CAPITAL
    
    async def fetch_historical_data(self, hours: int) -> pd.DataFrame:
        """
        Télécharge les données historiques depuis Binance
        
        Args:
            hours: Nombre d'heures de données à télécharger
            
        Returns:
            DataFrame avec les données OHLCV
        """
        logger.info(f"🏦 Téléchargement de {hours}h de données BTC/USDT...")
        
        limit = hours
        since = self.exchange.milliseconds() - (limit * 3600 * 1000)
        all_ohlcv = []
        
        max_iterations = (hours // 1000) + 2
        iteration = 0
        
        while len(all_ohlcv) < limit and iteration < max_iterations:
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    'BTC/USDT',
                    TIMEFRAME,
                    limit=1000,
                    since=since
                )
                
                if len(ohlcv) == 0:
                    logger.warning("Aucune donnée reçue de l'API")
                    break
                
                since = ohlcv[-1][0] + 1
                all_ohlcv += ohlcv
                await asyncio.sleep(0.05)
                iteration += 1
                
            except ccxt.NetworkError as e:
                logger.error(f"Erreur réseau lors du téléchargement : {e}")
                await asyncio.sleep(1)
                
            except ccxt.ExchangeError as e:
                logger.error(f"Erreur de l'exchange : {e}")
                break
                
            except Exception as e:
                logger.error(f"Erreur inattendue : {e}")
                break
        
        if not all_ohlcv:
            raise ValueError("Aucune donnée n'a pu être téléchargée")
        
        df = pd.DataFrame(
            all_ohlcv,
            columns=['time', 'open', 'high', 'low', 'close', 'volume']
        )
        
        logger.info(f"✅ {len(df)} bougies téléchargées")
        return df
    
    def run_simulation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Exécute la simulation de backtest sur les données.
        
        CORRECTION v8.1 : Utilise high/low pour détecter SL/TP (comme backtest.py).
        L'ancienne version utilisait check_exit(close), ce qui ratait les SL/TP
        touchés en intra-bougie et rendait les résultats SHORT optimistes.
        
        Args:
            df: DataFrame avec données OHLCV
            
        Returns:
            Dict avec les résultats du backtest
        """
        df = SniperShortV11Strategy.add_indicators(df)
        
        balance = self.initial_capital
        trades = 0
        wins = 0
        
        # On commence après 200 bougies (nécessaires pour l'EMA 200)
        i = 200
        
        while i < len(df) - 1:
            current_candle = df.iloc[i]
            previous_candle = df.iloc[i - 1]
            
            # Vérifier signal d'entrée SHORT
            if SniperShortV11Strategy.check_signal(current_candle, previous_candle):
                entry_price = current_candle['close']
                levels = SniperShortV11Strategy.calculate_levels(entry_price)
                
                outcome = None
                exit_index = i
                
                for j in range(i + 1, len(df)):
                    future_candle = df.iloc[j]
                    
                    # CORRECTION v8.1 : utiliser high/low comme backtest.py et backtest_rsi.py.
                    # L'ancienne version appelait check_exit(future_candle['close'], ...)
                    # ce qui ratait tous les SL/TP touchés intra-bougie si le close
                    # revenait de l'autre côté — résultats SHORT trop optimistes.
                    #
                    # Pour un SHORT :
                    #   SL = prix monte → touché si HIGH >= stop_loss
                    #   TP = prix descend → touché si LOW <= take_profit
                    if future_candle['high'] >= levels['stop_loss']:
                        outcome = "LOSS"
                        pnl = -(balance * RISK_PER_TRADE)
                        balance += pnl
                        exit_index = j
                        break
                    elif future_candle['low'] <= levels['take_profit']:
                        outcome = "WIN"
                        pnl = balance * (RISK_PER_TRADE * REWARD_RATIO)
                        balance += pnl
                        exit_index = j
                        break
                
                if outcome:
                    trades += 1
                    if outcome == "WIN":
                        wins += 1
                    i = exit_index
            
            i += 1
        
        # Calcul des métriques
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
    
    async def run_backtest(self, hours: int, progress_callback=None) -> str:
        """
        Lance un backtest complet et retourne le rapport formaté
        
        Args:
            hours: Nombre d'heures à backtester
            progress_callback: Fonction async pour mettre à jour le statut
            
        Returns:
            Rapport du backtest formaté en markdown
        """
        try:
            if progress_callback:
                await progress_callback(
                    f"⏳ **Téléchargement de {hours}h de données...**\n"
                    f"_(Cela peut prendre quelques secondes)_"
                )
            
            df = await self.fetch_historical_data(hours)
            
            if progress_callback:
                await progress_callback(
                    f"⚔️ **Simulation SHORT V11 (Vol Filter) sur {len(df)} bougies...**"
                )
            
            results = self.run_simulation(df)
            
            report = self._format_report(hours, results)
            
            logger.info(f"Backtest SHORT terminé : {results['total_trades']} trades, WR: {results['win_rate']:.1f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest SHORT : {e}", exc_info=True)
            return f"❌ **Erreur Backtest SHORT**\n\n{str(e)}"
    
    def _format_report(self, hours: int, results: Dict[str, Any]) -> str:
        """Formate les résultats en rapport lisible"""
        return (
            f"🧪 **RÉSULTAT BACKTEST SHORT ({hours}H)**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Départ :** {self.initial_capital:.2f} $\n"
            f"💰 **Final :** {results['final_balance']:.2f} $\n"
            f"📈 **P&L :** {results['pnl_dollars']:+.2f} $ ({results['pnl_percent']:+.1f}%)\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Trades :** {results['wins']} Wins / {results['total_trades']} Total\n"
            f"🎯 **Win Rate :** {results['win_rate']:.1f}%\n"
            "🔎 **Filtre Volume :** ACTIF"
        )
