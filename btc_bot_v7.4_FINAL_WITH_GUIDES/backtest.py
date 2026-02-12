"""
Moteur de backtest pour la stratÃ©gie Sniper V11
"""
import ccxt
import pandas as pd
import asyncio
import logging
from typing import Dict, Any
from strategies.sniper_v11 import SniperV11Strategy
from config import TIMEFRAME, BACKTEST_INITIAL_CAPITAL, RISK_PER_TRADE, REWARD_RATIO

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Moteur de simulation de backtest"""
    
    def __init__(self):
        self.exchange = ccxt.binance()
        self.initial_capital = BACKTEST_INITIAL_CAPITAL
    
    async def fetch_historical_data(self, hours: int) -> pd.DataFrame:
        """
        TÃ©lÃ©charge les donnÃ©es historiques depuis Binance
        
        Args:
            hours: Nombre d'heures de donnÃ©es Ã  tÃ©lÃ©charger
            
        Returns:
            DataFrame avec les donnÃ©es OHLCV
        """
        logger.info(f"🏦“¥ TÃ©lÃ©chargement de {hours}h de donnÃ©es BTC/USDT...")
        
        limit = hours
        since = self.exchange.milliseconds() - (limit * 3600 * 1000)
        all_ohlcv = []
        
        max_iterations = (hours // 1000) + 2  # SÃ©curitÃ© anti-boucle infinie
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
                    logger.warning("Aucune donnÃ©e reÃ§ue de l'API")
                    break
                
                since = ohlcv[-1][0] + 1
                all_ohlcv += ohlcv
                
                # Rate limiting
                await asyncio.sleep(0.05)
                iteration += 1
                
            except ccxt.NetworkError as e:
                logger.error(f"Erreur rÃ©seau lors du tÃ©lÃ©chargement : {e}")
                await asyncio.sleep(1)
                
            except ccxt.ExchangeError as e:
                logger.error(f"Erreur de l'exchange : {e}")
                break
                
            except Exception as e:
                logger.error(f"Erreur inattendue : {e}")
                break
        
        if not all_ohlcv:
            raise ValueError("Aucune donnÃ©e n'a pu Ãªtre tÃ©lÃ©chargÃ©e")
        
        df = pd.DataFrame(
            all_ohlcv,
            columns=['time', 'open', 'high', 'low', 'close', 'volume']
        )
        
        logger.info(f"âœ… {len(df)} bougies tÃ©lÃ©chargÃ©es")
        return df
    
    def run_simulation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        ExÃ©cute la simulation de backtest sur les donnÃ©es
        
        Args:
            df: DataFrame avec donnÃ©es OHLCV
            
        Returns:
            Dict avec les rÃ©sultats du backtest
        """
        # Ajouter les indicateurs
        df = SniperV11Strategy.add_indicators(df)
        
        balance = self.initial_capital
        trades = 0
        wins = 0
        
        # On commence aprÃ¨s 200 bougies (nÃ©cessaires pour l'EMA 200)
        i = 200
        
        while i < len(df) - 1:
            current_candle = df.iloc[i]
            previous_candle = df.iloc[i - 1]
            
            # VÃ©rifier signal d'entrÃ©e
            if SniperV11Strategy.check_signal(current_candle, previous_candle):
                entry_price = current_candle['close']
                levels = SniperV11Strategy.calculate_levels(entry_price)
                
                # Simuler le futur pour voir l'issue du trade
                outcome = None
                exit_index = i
                
                for j in range(i + 1, len(df)):
                    future_candle = df.iloc[j]
                    
                    # IMPORTANT : On vÃ©rifie les HIGH et LOW, pas juste le close
                    # pour Ã©viter de rater un stop qui a Ã©tÃ© touchÃ© pendant la bougie
                    if future_candle['low'] <= levels['stop_loss']:
                        outcome = "LOSS"
                        pnl = -(balance * RISK_PER_TRADE)
                        balance += pnl
                        exit_index = j
                        break
                    elif future_candle['high'] >= levels['take_profit']:
                        outcome = "WIN"
                        pnl = balance * (RISK_PER_TRADE * REWARD_RATIO)
                        balance += pnl
                        exit_index = j
                        break
                
                if outcome:
                    trades += 1
                    if outcome == "WIN":
                        wins += 1
                    i = exit_index  # On saute au moment de la sortie
            
            i += 1
        
        # Calcul des mÃ©triques
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
        Lance un backtest complet et retourne le rapport formatÃ©
        
        Args:
            hours: Nombre d'heures Ã  backtester
            progress_callback: Fonction async pour mettre Ã  jour le statut
            
        Returns:
            Rapport du backtest formatÃ© en markdown
        """
        try:
            # Ã‰tape 1 : TÃ©lÃ©chargement
            if progress_callback:
                await progress_callback(
                    f"â³ **TÃ©lÃ©chargement de {hours}h de donnÃ©es...**\n"
                    f"_(Cela peut prendre quelques secondes)_"
                )
            
            df = await self.fetch_historical_data(hours)
            
            # Ã‰tape 2 : Simulation
            if progress_callback:
                await progress_callback(
                    f"âš”ï¸ **Simulation V11 (Vol Filter) sur {len(df)} bougies...**"
                )
            
            results = self.run_simulation(df)
            
            # Ã‰tape 3 : GÃ©nÃ©ration du rapport
            report = self._format_report(hours, results)
            
            logger.info(f"Backtest terminÃ© : {results['total_trades']} trades, WR: {results['win_rate']:.1f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest : {e}", exc_info=True)
            return f"âŒ **Erreur Backtest**\n\n{str(e)}"
    
    def _format_report(self, hours: int, results: Dict[str, Any]) -> str:
        """Formate les rÃ©sultats en rapport lisible"""
        return (
            f"🧪 **RÃ‰SULTAT BACKTEST ({hours}H)**\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"🏦 **DÃ©part :** {self.initial_capital:.2f} $\n"
            f"🏦’° **Final :** {results['final_balance']:.2f} $\n"
            f"🏦“ˆ **P&L :** {results['pnl_dollars']:+.2f} $ ({results['pnl_percent']:+.1f}%)\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"🏦Ž² **Trades :** {results['wins']} Wins / {results['total_trades']} Total\n"
            f"🏦† **Win Rate :** {results['win_rate']:.1f}%\n"
            "🏦”’ **Filtre Volume :** ACTIF"
        )
