"""
Keyboards et boutons pour l'interface Telegram
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Dict, Any


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Keyboard principal du dashboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📉 Stratégies & Plans", callback_data='menu_strategies')],
        [InlineKeyboardButton("📊 Performance & Historique", callback_data='menu_history')],
        [InlineKeyboardButton("♻️ Actualiser", callback_data='refresh')],
        [InlineKeyboardButton("🛑 Éteindre le Bot", callback_data='ask_stop')]
    ])


def get_strategies_keyboard(sniper_active: bool, sniper_short_active: bool, rsi_active: bool) -> InlineKeyboardMarkup:
    """
    Keyboard de gestion des stratégies
    
    Args:
        sniper_active: État de la stratégie Sniper LONG
        sniper_short_active: État de la stratégie Sniper SHORT
        rsi_active: État de la stratégie RSI Bollinger
    """
    sniper_icon = "🟢" if sniper_active else "🔴"
    short_icon = "🟢" if sniper_short_active else "🔴"
    rsi_icon = "🟢" if rsi_active else "🔴"
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"{sniper_icon} Sniper V11 LONG",
                callback_data='toggle_sniper'
            ),
            InlineKeyboardButton("ℹ️", callback_data='info_sniper')
        ],
        [
            InlineKeyboardButton(
                f"{short_icon} Sniper V11 SHORT",
                callback_data='toggle_short'
            ),
            InlineKeyboardButton("ℹ️", callback_data='info_short')
        ],
        [
            InlineKeyboardButton(
                f"{rsi_icon} RSI Bollinger 15m",
                callback_data='toggle_rsi'
            ),
            InlineKeyboardButton("ℹ️", callback_data='info_rsi')
        ],
        [InlineKeyboardButton("🧪 Backtest Multi", callback_data='menu_backtest_multi')],
        [InlineKeyboardButton("⬅️ Retour Dashboard", callback_data='back_to_dash')]
    ])


def get_info_keyboard() -> InlineKeyboardMarkup:
    """Keyboard de la page d'information stratégie LONG"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧪 Lancer Backtest", callback_data='menu_backtest_duration')],
        [InlineKeyboardButton("⬅️ Retour", callback_data='menu_strategies')]
    ])


def get_info_short_keyboard() -> InlineKeyboardMarkup:
    """Keyboard de la page d'information stratégie SHORT"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧪 Lancer Backtest", callback_data='menu_backtest_duration_short')],
        [InlineKeyboardButton("⬅️ Retour", callback_data='menu_strategies')]
    ])


def get_info_rsi_keyboard() -> InlineKeyboardMarkup:
    """Keyboard de la page d'information stratégie RSI Bollinger"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧪 Lancer Backtest", callback_data='menu_backtest_duration_rsi')],
        [InlineKeyboardButton("⬅️ Retour", callback_data='menu_strategies')]
    ])


def get_backtest_duration_keyboard() -> InlineKeyboardMarkup:
    """Keyboard de sélection de durée de backtest pour LONG"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1 Mois", callback_data='bt_run_720'),
            InlineKeyboardButton("6 Mois", callback_data='bt_run_4300')
        ],
        [
            InlineKeyboardButton("1 An", callback_data='bt_run_8760'),
            InlineKeyboardButton("✏️ Personnalisé", callback_data='bt_custom_input')
        ],
        [InlineKeyboardButton("⬅️ Retour", callback_data='info_sniper')]
    ])


def get_backtest_duration_short_keyboard() -> InlineKeyboardMarkup:
    """Keyboard de sélection de durée de backtest pour SHORT"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1 Mois", callback_data='bts_run_720'),
            InlineKeyboardButton("6 Mois", callback_data='bts_run_4300')
        ],
        [
            InlineKeyboardButton("1 An", callback_data='bts_run_8760'),
            InlineKeyboardButton("✏️ Personnalisé", callback_data='bts_custom_input')
        ],
        [InlineKeyboardButton("⬅️ Retour", callback_data='info_short')]
    ])


def get_backtest_duration_rsi_keyboard() -> InlineKeyboardMarkup:
    """Keyboard de sélection de durée de backtest pour RSI (en bougies 15min)"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1 Mois (2880)", callback_data='btr_run_2880'),
            InlineKeyboardButton("6 Mois (17280)", callback_data='btr_run_17280')
        ],
        [
            InlineKeyboardButton("1 An (35040)", callback_data='btr_run_35040'),
            InlineKeyboardButton("✏️ Personnalisé", callback_data='btr_custom_input')
        ],
        [InlineKeyboardButton("⬅️ Retour", callback_data='info_rsi')]
    ])


def get_back_keyboard(target: str = 'back_to_dash') -> InlineKeyboardMarkup:
    """
    Keyboard simple avec bouton retour
    
    Args:
        target: Callback data du bouton retour
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Retour", callback_data=target)]
    ])


def get_confirm_stop_keyboard() -> InlineKeyboardMarkup:
    """Keyboard de confirmation d'arrêt du bot"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ OUI, ÉTEINDRE", callback_data='confirm_stop')],
        [InlineKeyboardButton("⬅️ NON, RETOUR", callback_data='back_to_dash')]
    ])


def get_backtest_multi_selection_keyboard(sniper_selected: bool, short_selected: bool, rsi_selected: bool) -> InlineKeyboardMarkup:
    """
    Keyboard de sélection des stratégies pour backtest multi
    
    Args:
        sniper_selected: Si Sniper LONG est sélectionné
        short_selected: Si Sniper SHORT est sélectionné
        rsi_selected: Si RSI Bollinger est sélectionné
    """
    sniper_icon = "✅" if sniper_selected else "❌"
    short_icon = "✅" if short_selected else "❌"
    rsi_icon = "✅" if rsi_selected else "❌"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{sniper_icon} Sniper V11 LONG (1H)", callback_data='btm_toggle_sniper')],
        [InlineKeyboardButton(f"{short_icon} Sniper V11 SHORT (1H)", callback_data='btm_toggle_short')],
        [InlineKeyboardButton(f"{rsi_icon} RSI Bollinger (15min)", callback_data='btm_toggle_rsi')],
        [InlineKeyboardButton("➡️ Suivant", callback_data='btm_next')],
        [InlineKeyboardButton("⬅️ Retour", callback_data='menu_strategies')]
    ])


def get_backtest_multi_mode_keyboard() -> InlineKeyboardMarkup:
    """Keyboard de sélection du mode de trading pour backtest multi"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ Séquentiel (un trade à la fois)", callback_data='btm_mode_seq')],
        [InlineKeyboardButton("🔀 Parallèle (trades simultanés)", callback_data='btm_mode_par')],
        [InlineKeyboardButton("⬅️ Retour", callback_data='menu_backtest_multi')]
    ])


def get_backtest_multi_duration_keyboard() -> InlineKeyboardMarkup:
    """Keyboard de sélection de durée pour backtest multi"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1 Mois", callback_data='btm_run_720'),
            InlineKeyboardButton("6 Mois", callback_data='btm_run_4300')
        ],
        [
            InlineKeyboardButton("1 An", callback_data='btm_run_8760'),
            InlineKeyboardButton("✏️ Personnalisé", callback_data='btm_custom_input')
        ],
        [InlineKeyboardButton("⬅️ Retour", callback_data='btm_select_mode')]
    ])
