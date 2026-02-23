"""
Messages et textes formatés pour l'interface Telegram
"""
from datetime import datetime
from typing import Dict, Any, List
from config import INITIAL_CAPITAL, RISK_PER_TRADE, REWARD_RATIO


def get_dashboard_text(db_data: Dict[str, Any]) -> str:
    """
    Génère le texte du dashboard principal
    
    Args:
        db_data: Données de la base de données
    """
    active_trade = "✅ EN COURS" if db_data.get('current_trade') else "💤 REPOS"
    
    # Compteur de stratégies actives
    nb_active = sum(1 for v in db_data.get('strategies', {}).values() if v)
    
    return (
        "🎛️ **BTC Trader Bot V8**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🤖 **Système :** EN LIGNE\n"
        f"🔫 **Stratégies Actives :** {nb_active}\n"
        f"🔄 **Statut Trade :** {active_trade}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sélectionne une action :"
    )


def get_history_text(db_data: Dict[str, Any]) -> str:
    """
    Génère le rapport de performance et l'historique
    
    Args:
        db_data: Données de la base de données
    """
    trades = db_data.get('trades', [])
    balance = db_data.get('balance', INITIAL_CAPITAL)
    
    total_trades = len(trades)
    wins = len([t for t in trades if t.get('result') == "WIN"])
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    pnl_dollars = balance - INITIAL_CAPITAL
    pnl_percent = (pnl_dollars / INITIAL_CAPITAL) * 100
    emoji_pnl = "🟢" if pnl_dollars >= 0 else "🔴"
    
    text = (
        "📊 **RAPPORT DE PERFORMANCE**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Capital Actuel :** {balance:.2f} $\n"
        f"🏁 **Départ :** {INITIAL_CAPITAL} $\n"
        f"{emoji_pnl} **P&L Total :** {pnl_dollars:+.2f} $ ({pnl_percent:+.2f}%)\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🎲 **Total Trades :** {total_trades}\n"
        f"🏆 **Win Rate :** {win_rate:.1f}%\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📜 **HISTORIQUE RÉCENT :**\n"
    )
    
    if not trades:
        text += "Aucun trade archivé."
    else:
        # Afficher les 5 derniers trades
        for trade in reversed(trades[-5:]):
            res_icon = "✅" if trade.get('result') == "WIN" else "❌"
            profit = trade.get('profit_loss', 0)
            
            # Format de la date
            entry_dt = datetime.fromisoformat(trade['entry_time']).strftime('%d/%m %H:%M')
            strat_name = trade.get('strategy', 'Sniper EMA')
            
            text += (
                f"{res_icon} **{strat_name}**\n"
                f"📅 {entry_dt} | ⚖️ R:R 1:{REWARD_RATIO}\n"
                f"📥 In: {trade['entry_price']:.2f}$ | 📤 Out: {trade['exit_price']:.2f}$\n"
                f"💵 **P&L : {profit:+.2f} $**\n"
                "───────────────\n"
            )
    
    return text


def get_strategy_info_text() -> str:
    """Texte d'information sur la stratégie Sniper V11"""
    return (
        "ℹ️ **DÉTAILS STRATÉGIE : SNIPER EMA V11**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📈 **Indicateur :** EMA 200 + Volume MA 20\n"
        "⏱️ **Unité de temps :** 1H (Bougies d'une heure)\n\n"
        "⚡ **LOGIQUE DU DÉCLENCHEUR :**\n"
        "Le bot analyse les bougies CLÔTURÉES.\n"
        "1️⃣ **EMA :** Le prix doit casser l'EMA 200 à la hausse.\n"
        "2️⃣ **VOLUME :** Le volume de la bougie doit être > Moyenne 20.\n"
        "👉 **Breakout Confirmé par le Volume**.\n\n"
        "🛡️ **GESTION V11 (TIGHT) :**\n"
        f"• **Stop Loss :** -{RISK_PER_TRADE*100:.1f}% (Serré)\n"
        f"• **Take Profit :** +{RISK_PER_TRADE*REWARD_RATIO*100:.1f}% (Cible 1:3)\n"
        "• **Philosophie :** Sécurité maximale. On filtre les mouvements mous."
    )


def get_strategies_menu_text() -> str:
    """Texte du menu de gestion des stratégies"""
    return "📂 **GESTIONNAIRE DE STRATÉGIES**"


def get_backtest_duration_menu_text() -> str:
    """Texte du menu de sélection de durée de backtest"""
    return "🧪 **CHOISIS LA DURÉE DU TEST :**"


def get_custom_backtest_input_text() -> str:
    """Texte pour l'input personnalisé de backtest"""
    return (
        "✍️ **BACKTEST PERSONNALISÉ**\n\n"
        "Envoyez-moi le nombre d'heures souhaité dans le chat (ex: 5000).\n\n"
        "_Tapez n'importe quoi d'autre pour annuler._"
    )


def get_confirm_stop_text() -> str:
    """Texte de confirmation d'arrêt"""
    return "⚠️ **CONFIRMATION**\nCouper le serveur ?"


def get_invalid_number_text() -> str:
    """Message d'erreur pour nombre invalide"""
    return "❌ Nombre invalide. Retour au menu."


def get_strategy_short_info_text() -> str:
    """Texte d'information sur la stratégie Sniper SHORT V11"""
    return (
        "ℹ️ **DÉTAILS STRATÉGIE : SNIPER SHORT V11**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📈 **Indicateur :** EMA 200 + Volume MA 20\n"
        "⏱️ **Unité de temps :** 1H (Bougies d'une heure)\n"
        "📉 **Direction :** SHORT (Vente à découvert)\n\n"
        "⚡ **LOGIQUE DU DÉCLENCHEUR :**\n"
        "Le bot analyse les bougies CLÔTURÉES.\n"
        "1️⃣ **EMA :** Le prix doit casser l'EMA 200 à la BAISSE.\n"
        "2️⃣ **VOLUME :** Le volume de la bougie doit être > Moyenne 20.\n"
        "👉 **Breakout Baissier Confirmé par le Volume**.\n\n"
        "🛡️ **GESTION V11 (TIGHT) :**\n"
        f"• **Stop Loss :** +{RISK_PER_TRADE*100:.1f}% (Prix monte = perte)\n"
        f"• **Take Profit :** -{RISK_PER_TRADE*REWARD_RATIO*100:.1f}% (Prix descend = gain)\n"
        "• **Ratio :** 1:3\n"
        "• **Philosophie :** Profiter des retournements baissiers."
    )


def get_strategy_rsi_info_text() -> str:
    """Texte d'information sur la stratégie RSI Bollinger 15min"""
    return (
        "ℹ️ **DÉTAILS STRATÉGIE : RSI BOLLINGER 15MIN**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 **Indicateurs :** RSI(14) + Bollinger Bands(25,2)\n"
        "⏰ **Unité de temps :** 15 MINUTES\n"
        "📈 **Win Rate Documenté :** 78-82%\n\n"
        "⚡ **LOGIQUE DU DÉCLENCHEUR :**\n"
        "**LONG :**\n"
        "1️⃣ Prix touche/traverse Bande Bollinger INFÉRIEURE\n"
        "2️⃣ RSI < 30 (Survente)\n"
        "3️⃣ Volume > Moyenne 20\n\n"
        "**SHORT :**\n"
        "1️⃣ Prix touche/traverse Bande Bollinger SUPÉRIEURE\n"
        "2️⃣ RSI > 70 (Surachat)\n"
        "3️⃣ Volume > Moyenne 20\n\n"
        "🛡️ **GESTION :**\n"
        "• **Stop Loss :** -1.5%\n"
        "• **Take Profit :** +4.5% (Ratio 1:3)\n"
        "• **Philosophie :** Retournements sur zones extrêmes"
    )


def format_trade_entry_notification(entry_price: float) -> str:
    """
    Message de notification d'entrée en position
    
    Args:
        entry_price: Prix d'entrée
    """
    return f"🎯 **SIGNAL V11 (Vol Validé)**\nEntrée: {entry_price:.2f}$"


def format_stop_loss_notification(loss: float) -> str:
    """
    Message de notification de Stop Loss
    
    Args:
        loss: Montant de la perte
    """
    return f"❌ **STOP LOSS**\nPerte: {loss:.2f}$"


def format_take_profit_notification(gain: float) -> str:
    """
    Message de notification de Take Profit
    
    Args:
        gain: Montant du gain
    """
    return f"✅ **TAKE PROFIT**\nGain: {gain:.2f}$"
