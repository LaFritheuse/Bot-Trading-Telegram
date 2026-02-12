"""
Moteur de backtest multi-stratÃ©gies
"""
import ccxt
import pandas as pd
import asyncio
import logging
from typing import Dict, Any, List
from strategies.sniper_v11 import SniperV11Strategy
from strategies.sniper_short_v11 import SniperShortV11Strategy
from strategies.rsi_bollinger_15m import RSIBollingerStrategy
from config import TIMEFRAME, BACKTEST_INITIAL_CAPITAL, RISK_PER_TRADE, REWARD_RATIO

logger = logging.getLogger(__name__)


class BacktestMultiEngine:
    """Moteur de simulation de backtest multi-stratÃ©gies"""
    
    def __init__(self):
        self.exchange = ccxt.binance()
        self.initial_capital = BACKTEST_INITIAL_CAPITAL
        
        # Mapping des stratÃ©gies
        self.strategies = {
            'sniper_ema': SniperV11Strategy,
            'sniper_short': SniperShortV11Strategy
        }
    
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
                    break
                
                since = ohlcv[-1][0] + 1
                all_ohlcv += ohlcv
                await asyncio.sleep(0.05)
                iteration += 1
                
            except Exception as e:
                logger.error(f"Erreur tÃ©lÃ©chargement : {e}")
                break
        
        if not all_ohlcv:
            raise ValueError("Aucune donnÃ©e tÃ©lÃ©chargÃ©e")
        
        df = pd.DataFrame(
            all_ohlcv,
            columns=['time', 'open', 'high', 'low', 'close', 'volume']
        )
        
        logger.info(f"âœ… {len(df)} bougies tÃ©lÃ©chargÃ©es")
        return df
    
    def run_simulation_sequential(
        self, 
        df: pd.DataFrame, 
        active_strategies: List[str]
    ) -> Dict[str, Any]:
        """
        ExÃ©cute la simulation en mode SÃ‰QUENTIEL
        Une seule position ouverte Ã  la fois, premier signal = prioritÃ©
        
        Args:
            df: DataFrame avec donnÃ©es OHLCV
            active_strategies: Liste des stratÃ©gies Ã  tester
            
        Returns:
            Dict avec les rÃ©sultats du backtest
        """
        # PrÃ©parer les DataFrames avec indicateurs pour chaque stratÃ©gie
        dfs = {}
        for strat_key in active_strategies:
            StrategyClass = self.strategies[strat_key]
            dfs[strat_key] = StrategyClass.add_indicators(df.copy())
        
        balance = self.initial_capital
        trades = 0
        wins = 0
        trades_by_strategy = {key: {'total': 0, 'wins': 0} for key in active_strategies}
        
        i = 200  # Commencer aprÃ¨s EMA 200
        
        while i < len(df) - 1:
            # VÃ©rifier chaque stratÃ©gie dans l'ordre
            for strat_key in active_strategies:
                StrategyClass = self.strategies[strat_key]
                df_strat = dfs[strat_key]
                
                current_candle = df_strat.iloc[i]
                previous_candle = df_strat.iloc[i - 1]
                
                # VÃ©rifier signal d'entrÃ©e
                if StrategyClass.check_signal(current_candle, previous_candle):
                    entry_price = current_candle['close']
                    levels = StrategyClass.calculate_levels(entry_price)
                    
                    # Simuler le futur
                    outcome = None
                    exit_index = i
                    
                    for j in range(i + 1, len(df)):
                        future_candle = df.iloc[j]
                        
                        # CrÃ©er un trade temporaire pour check_exit
                        temp_trade = {
                            'stop_loss': levels['stop_loss'],
                            'take_profit': levels['take_profit']
                        }
                        
                        # IMPORTANT : Vérifier high/low pour cohérence
                        if future_candle['low'] <= temp_trade['stop_loss']:
                            outcome = "LOSS"
                            exit_index = j
                            break
                        elif future_candle['high'] >= temp_trade['take_profit']:
                            outcome = "WIN"
                            exit_index = j
                            break
                    
                    if outcome:
                        trades += 1
                        trades_by_strategy[strat_key]['total'] += 1
                        
                        if outcome == "WIN":
                            pnl = balance * (RISK_PER_TRADE * REWARD_RATIO)
                            wins += 1
                            trades_by_strategy[strat_key]['wins'] += 1
                        else:
                            pnl = -(balance * RISK_PER_TRADE)
                        
                        balance += pnl
                        i = exit_index
                        break  # Sortir de la boucle des stratÃ©gies, on a pris un trade
            
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
            'win_rate': win_rate,
            'trades_by_strategy': trades_by_strategy,
            'mode': 'sequential'
        }
    
    def run_simulation_parallel(
        self, 
        df: pd.DataFrame, 
        active_strategies: List[str]
    ) -> Dict[str, Any]:
        """
        ExÃ©cute la simulation en mode PARALLÃˆLE
        Chaque stratÃ©gie trade indÃ©pendamment avec le CAPITAL COMPLET
        
        Args:
            df: DataFrame avec donnÃ©es OHLCV
            active_strategies: Liste des stratÃ©gies Ã  tester
            
        Returns:
            Dict avec les rÃ©sultats du backtest
        """
        # CORRECTION : Chaque stratÃ©gie a le capital COMPLET, pas divisÃ©
        capital_per_strategy = self.initial_capital
        
        results_by_strategy = {}
        
        # Backtester chaque stratÃ©gie indÃ©pendamment
        for strat_key in active_strategies:
            StrategyClass = self.strategies[strat_key]
            df_strat = StrategyClass.add_indicators(df.copy())
            
            balance = capital_per_strategy
            trades = 0
            wins = 0
            
            i = 200
            
            while i < len(df) - 1:
                current_candle = df_strat.iloc[i]
                previous_candle = df_strat.iloc[i - 1]
                
                if StrategyClass.check_signal(current_candle, previous_candle):
                    entry_price = current_candle['close']
                    levels = StrategyClass.calculate_levels(entry_price)
                    
                    outcome = None
                    exit_index = i
                    
                    for j in range(i + 1, len(df)):
                        future_candle = df.iloc[j]
                        
                        temp_trade = {
                            'stop_loss': levels['stop_loss'],
                            'take_profit': levels['take_profit']
                        }
                        
                        # IMPORTANT : Vérifier high/low pour cohérence
                        if future_candle['low'] <= temp_trade['stop_loss']:
                            outcome = "LOSS"
                            exit_index = j
                            break
                        elif future_candle['high'] >= temp_trade['take_profit']:
                            outcome = "WIN"
                            exit_index = j
                            break
                    
                    if outcome:
                        trades += 1
                        if outcome == "WIN":
                            pnl = balance * (RISK_PER_TRADE * REWARD_RATIO)
                            wins += 1
                        else:
                            pnl = -(balance * RISK_PER_TRADE)
                        
                        balance += pnl
                        i = exit_index
                
                i += 1
            
            results_by_strategy[strat_key] = {
                'final_balance': balance,
                'initial_balance': capital_per_strategy,
                'total': trades,
                'wins': wins,
                'losses': trades - wins,
                'win_rate': (wins / trades * 100) if trades > 0 else 0
            }
        
        # AgrÃ©ger les rÃ©sultats - MOYENNE des performances
        avg_final_balance = sum(r['final_balance'] for r in results_by_strategy.values()) / len(results_by_strategy)
        total_trades = sum(r['total'] for r in results_by_strategy.values())
        total_wins = sum(r['wins'] for r in results_by_strategy.values())
        
        pnl_dollars = avg_final_balance - self.initial_capital
        pnl_percent = (pnl_dollars / self.initial_capital) * 100
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'final_balance': avg_final_balance,
            'pnl_dollars': pnl_dollars,
            'pnl_percent': pnl_percent,
            'total_trades': total_trades,
            'wins': total_wins,
            'losses': total_trades - total_wins,
            'win_rate': win_rate,
            'results_by_strategy': results_by_strategy,
            'mode': 'parallel'
        }
    
    async def run_backtest(
        self, 
        hours: int, 
        active_strategies: List[str],
        mode: str,
        progress_callback=None
    ) -> str:
        """
        Lance un backtest multi-stratÃ©gies
        
        Args:
            hours: Nombre d'heures Ã  backtester
            active_strategies: Liste des clÃ©s de stratÃ©gies actives
            mode: 'sequential' ou 'parallel'
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
                mode_text = "SÃ©quentiel" if mode == "sequential" else "ParallÃ¨le"
                await progress_callback(
                    f"âš”ï¸ **Simulation Multi ({mode_text}) sur {len(df)} bougies...**"
                )
            
            if mode == "sequential":
                results = self.run_simulation_sequential(df, active_strategies)
            else:
                results = self.run_simulation_parallel(df, active_strategies)
            
            # Ã‰tape 3 : GÃ©nÃ©ration du rapport
            report = self._format_report(hours, results, active_strategies)
            
            logger.info(f"Backtest Multi terminÃ© : {results['total_trades']} trades, WR: {results['win_rate']:.1f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest multi : {e}", exc_info=True)
            return f"âŒ **Erreur Backtest Multi**\n\n{str(e)}"
    
    def _format_report(self, hours: int, results: Dict[str, Any], active_strategies: List[str]) -> str:
        """Formate les rÃ©sultats en rapport lisible avec comparaison visuelle"""
        
        mode_text = "SÃ©quentiel (1 trade Ã  la fois)" if results['mode'] == 'sequential' else "ParallÃ¨le (trades simultanÃ©s)"
        
        # Nom des stratÃ©gies
        strategy_names = {
            'sniper_ema': 'LONG',
            'sniper_short': 'SHORT'
        }
        
        strat_list = " + ".join([strategy_names.get(s, s) for s in active_strategies])
        
        report = (
            f"🧪 **BACKTEST MULTI ({hours}H)**\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"🏦“Š **StratÃ©gies :** {strat_list}\n"
            f"🏦Ž® **Mode :** {mode_text}\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"🏦 **DÃ©part :** {self.initial_capital:.2f} $\n"
            f"🏦’° **Final :** {results['final_balance']:.2f} $\n"
            f"🏦“ˆ **P&L :** {results['pnl_dollars']:+.2f} $ ({results['pnl_percent']:+.1f}%)\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"🏦Ž² **Trades Totaux :** {results['wins']} Wins / {results['total_trades']} Total\n"
            f"🏦† **Win Rate Global :** {results['win_rate']:.1f}%\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        )
        
        # DÃ©tails par stratÃ©gie - Format visuel cÃ´te Ã  cÃ´te
        if results['mode'] == 'sequential':
            report += "🏦“Š **COMPARAISON PAR STRATÃ‰GIE :**\n\n"
            
            # En-tÃªtes
            if len(active_strategies) == 2:
                report += "```\n"
                report += f"{'LONG':^20} | {'SHORT':^20}\n"
                report += f"{'-'*20}-+-{'-'*20}\n"
                
                stats_long = results['trades_by_strategy'].get('sniper_ema', {'total': 0, 'wins': 0})
                stats_short = results['trades_by_strategy'].get('sniper_short', {'total': 0, 'wins': 0})
                
                wr_long = (stats_long['wins'] / stats_long['total'] * 100) if stats_long['total'] > 0 else 0
                wr_short = (stats_short['wins'] / stats_short['total'] * 100) if stats_short['total'] > 0 else 0
                
                # Ligne Trades
                report += f"{'Trades: ' + str(stats_long['total']):^20} | {'Trades: ' + str(stats_short['total']):^20}\n"
                
                # Ligne Wins
                report += f"{'Wins: ' + str(stats_long['wins']):^20} | {'Wins: ' + str(stats_short['wins']):^20}\n"
                
                # Ligne Win Rate
                report += f"{'WR: ' + f'{wr_long:.1f}%':^20} | {'WR: ' + f'{wr_short:.1f}%':^20}\n"
                
                report += "```\n"
            else:
                # Une seule stratÃ©gie
                for strat_key in active_strategies:
                    stats = results['trades_by_strategy'][strat_key]
                    name = strategy_names.get(strat_key, strat_key)
                    wr = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    report += f"â€¢ **{name}**: {stats['wins']}/{stats['total']} trades ({wr:.1f}%)\n"
        else:
            # Mode parallÃ¨le
            report += "🏦“Š **COMPARAISON PAR STRATÃ‰GIE :**\n\n"
            
            if len(active_strategies) == 2:
                report += "```\n"
                report += f"{'LONG':^20} | {'SHORT':^20}\n"
                report += f"{'-'*20}-+-{'-'*20}\n"
                
                stats_long = results['results_by_strategy'].get('sniper_ema', {
                    'final_balance': 0, 'initial_balance': 0, 'total': 0, 'wins': 0, 'win_rate': 0
                })
                stats_short = results['results_by_strategy'].get('sniper_short', {
                    'final_balance': 0, 'initial_balance': 0, 'total': 0, 'wins': 0, 'win_rate': 0
                })
                
                pnl_long = stats_long['final_balance'] - stats_long['initial_balance']
                pnl_short = stats_short['final_balance'] - stats_short['initial_balance']
                
                # Balance finale
                report += f"{'$' + f'{stats_long["final_balance"]:.0f}':^20} | {'$' + f'{stats_short["final_balance"]:.0f}':^20}\n"
                
                # P&L
                report += f"{f'{pnl_long:+.0f}$':^20} | {f'{pnl_short:+.0f}$':^20}\n"
                
                # Trades
                report += f"{'Trades: ' + str(stats_long['total']):^20} | {'Trades: ' + str(stats_short['total']):^20}\n"
                
                # Wins
                report += f"{'Wins: ' + str(stats_long['wins']):^20} | {'Wins: ' + str(stats_short['wins']):^20}\n"
                
                # Win Rate
                report += f"{'WR: ' + f'{stats_long["win_rate"]:.1f}%':^20} | {'WR: ' + f'{stats_short["win_rate"]:.1f}%':^20}\n"
                
                report += "```\n"
            else:
                # Une seule stratÃ©gie
                for strat_key in active_strategies:
                    stats = results['results_by_strategy'][strat_key]
                    name = strategy_names.get(strat_key, strat_key)
                    pnl = stats['final_balance'] - stats['initial_balance']
                    report += (
                        f"â€¢ **{name}**:\n"
                        f"  Balance: {stats['final_balance']:.2f}$ ({pnl:+.2f}$)\n"
                        f"  Trades: {stats['wins']}/{stats['total']} ({stats['win_rate']:.1f}%)\n"
                    )
        
        return report
