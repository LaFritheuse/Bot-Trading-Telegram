"""
Gestion des callbacks des boutons Telegram - Version Multi-Stratégies
"""
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from config import MY_CHAT_ID
from database import db
from backtest import BacktestEngine
from backtest_short import BacktestShortEngine
from backtest_rsi import BacktestRSIEngine
from ui.keyboards import (
    get_main_keyboard,
    get_strategies_keyboard,
    get_info_keyboard,
    get_info_short_keyboard,
    get_info_rsi_keyboard,
    get_backtest_duration_keyboard,
    get_backtest_duration_short_keyboard,
    get_backtest_duration_rsi_keyboard,
    get_back_keyboard,
    get_confirm_stop_keyboard
)
from ui.messages import (
    get_dashboard_text,
    get_history_text,
    get_strategy_info_text,
    get_strategy_short_info_text,
    get_strategy_rsi_info_text,
    get_strategies_menu_text,
    get_backtest_duration_menu_text,
    get_custom_backtest_input_text,
    get_confirm_stop_text,
    get_invalid_number_text
)

logger = logging.getLogger(__name__)


class CallbackHandler:
    """Gestionnaire des callbacks Telegram"""
    
    def __init__(self):
        self.backtest_engine = BacktestEngine()
        self.backtest_short_engine = BacktestShortEngine()
        self.backtest_rsi_engine = BacktestRSIEngine()
        self.user_state = {}  # Stockage temporaire pour inputs personnalisés
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Routeur principal des callbacks.
        
        CORRECTION v8.3 : Vérification owner-only.
        Sans cette vérification, n'importe qui connaissant le lien du bot
        pouvait stopper le bot, toggler les stratégies ou lancer des backtests.
        
        Args:
            update: Update Telegram
            context: Context Telegram
        """
        query = update.callback_query
        await query.answer()
        
        # CORRECTION v8.3 : vérification owner-only
        if query.message.chat_id != MY_CHAT_ID:
            logger.warning(f"Callback non autorisé refusé (chat_id={query.message.chat_id})")
            return
        
        data = query.data
        chat_id = query.message.chat_id
        
        # Nettoyage de l'état utilisateur (sauf pour les inputs custom)
        if data not in ['bt_custom_input', 'bts_custom_input', 'btr_custom_input']:
            if chat_id in self.user_state:
                del self.user_state[chat_id]

        logger.info(f"Callback reçu : {data} de l'utilisateur {chat_id}")
        
        # Backtest Multi supprimé (Btc_Bot_V8)
        if data == 'menu_backtest_multi' or data.startswith('btm_') or data.startswith('btm_run_'):
            db_data = db.load()
            sniper_active = db_data.get('strategies', {}).get('sniper_ema', True)
            sniper_short_active = db_data.get('strategies', {}).get('sniper_short', True)
            rsi_active = db_data.get('strategies', {}).get('rsi_bollinger', True)

            await query.edit_message_text(
                text="ℹ️ **Backtest Multi retiré dans Btc_Bot_V8**\n\n" + get_strategies_menu_text(),
                reply_markup=get_strategies_keyboard(sniper_active, sniper_short_active, rsi_active),
                parse_mode='Markdown'
            )
            return

        # Routage des callbacks
        handlers = {
            'back_to_dash': self._handle_back_to_dash,
            'refresh': self._handle_back_to_dash,
            'menu_strategies': self._handle_strategies_menu,
            'toggle_sniper': self._handle_toggle_sniper,
            'toggle_short': self._handle_toggle_short,
            'info_sniper': self._handle_strategy_info,
            'info_short': self._handle_strategy_short_info,
            'info_rsi': self._handle_strategy_rsi_info,
            'toggle_rsi': self._handle_toggle_rsi,
            'menu_backtest_duration': self._handle_backtest_duration_menu,
            'menu_backtest_duration_short': self._handle_backtest_duration_short_menu,
            'menu_backtest_duration_rsi': self._handle_backtest_duration_rsi_menu,
            'bt_custom_input': self._handle_custom_backtest_input,
            'bts_custom_input': self._handle_custom_backtest_short_input,
            'btr_custom_input': self._handle_custom_backtest_rsi_input,
            'menu_history': self._handle_history,
            'ask_stop': self._handle_ask_stop,
            'confirm_stop': self._handle_confirm_stop,
        }
        
        # Callbacks avec préfixes
        if data.startswith('bt_run_'):
            await self._handle_run_backtest(query, context, data)
        elif data.startswith('bts_run_'):
            await self._handle_run_backtest_short(query, context, data)
        elif data.startswith('btr_run_'):
            await self._handle_run_backtest_rsi(query, context, data)
        elif data in handlers:
            await handlers[data](query, context)
        else:
            logger.warning(f"Callback non géré : {data}")
    
    async def _handle_back_to_dash(self, query, context):
        """Retour au dashboard principal"""
        db_data = db.load()
        try:
            await query.edit_message_text(
                text=get_dashboard_text(db_data),
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )
        except BadRequest:
            pass
    
    async def _handle_strategies_menu(self, query, context):
        """Affiche le menu des stratégies"""
        db_data = db.load()
        sniper_active = db_data.get('strategies', {}).get('sniper_ema', True)
        sniper_short_active = db_data.get('strategies', {}).get('sniper_short', True)
        rsi_active = db_data.get('strategies', {}).get('rsi_bollinger', True)
        
        await query.edit_message_text(
            text=get_strategies_menu_text(),
            reply_markup=get_strategies_keyboard(sniper_active, sniper_short_active, rsi_active),
            parse_mode='Markdown'
        )
    
    async def _handle_toggle_sniper(self, query, context):
        """Active/désactive la stratégie Sniper LONG"""
        db.toggle_strategy('sniper_ema')
        await self._handle_strategies_menu(query, context)
    
    async def _handle_toggle_short(self, query, context):
        """Active/désactive la stratégie Sniper SHORT"""
        db.toggle_strategy('sniper_short')
        await self._handle_strategies_menu(query, context)
    
    async def _handle_strategy_info(self, query, context):
        """Affiche les informations de la stratégie LONG"""
        await query.edit_message_text(
            text=get_strategy_info_text(),
            reply_markup=get_info_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_strategy_short_info(self, query, context):
        """Affiche les informations de la stratégie SHORT"""
        await query.edit_message_text(
            text=get_strategy_short_info_text(),
            reply_markup=get_info_short_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_backtest_duration_menu(self, query, context):
        """Affiche le menu de sélection de durée pour LONG"""
        await query.edit_message_text(
            text=get_backtest_duration_menu_text(),
            reply_markup=get_backtest_duration_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_backtest_duration_short_menu(self, query, context):
        """Affiche le menu de sélection de durée pour SHORT"""
        await query.edit_message_text(
            text=get_backtest_duration_menu_text(),
            reply_markup=get_backtest_duration_short_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_run_backtest(self, query, context, data: str):
        """
        Lance un backtest avec une durée prédéfinie
        
        Args:
            data: Callback data (format: bt_run_HOURS)
        """
        try:
            hours = int(data.split('_')[2])
            chat_id = query.message.chat_id
            message_id = query.message.message_id
            
            async def update_status(text: str):
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode='Markdown'
                )
            
            report = await self.backtest_engine.run_backtest(hours, update_status)
            
            await query.edit_message_text(
                text=report,
                reply_markup=get_back_keyboard('menu_backtest_duration'),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest : {e}", exc_info=True)
            await query.edit_message_text(
                text=f"❌ Erreur lors du backtest : {str(e)}",
                reply_markup=get_back_keyboard('menu_backtest_duration'),
                parse_mode='Markdown'
            )
    
    async def _handle_custom_backtest_input(self, query, context):
        """Prépare l'input personnalisé pour le backtest LONG"""
        chat_id = query.message.chat_id
        
        self.user_state[chat_id] = {
            'state': 'WAITING_BACKTEST_HOURS',
            'menu_msg_id': query.message.message_id
        }
        
        await query.edit_message_text(
            text=get_custom_backtest_input_text(),
            parse_mode='Markdown'
        )
    
    async def _handle_run_backtest_short(self, query, context, data: str):
        """
        Lance un backtest SHORT avec une durée prédéfinie
        
        Args:
            data: Callback data (format: bts_run_HOURS)
        """
        try:
            hours = int(data.split('_')[2])
            chat_id = query.message.chat_id
            message_id = query.message.message_id
            
            async def update_status(text: str):
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode='Markdown'
                )
            
            report = await self.backtest_short_engine.run_backtest(hours, update_status)
            
            await query.edit_message_text(
                text=report,
                reply_markup=get_back_keyboard('menu_backtest_duration_short'),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest SHORT : {e}", exc_info=True)
            await query.edit_message_text(
                text=f"❌ Erreur lors du backtest SHORT : {str(e)}",
                reply_markup=get_back_keyboard('menu_backtest_duration_short'),
                parse_mode='Markdown'
            )
    
    async def _handle_custom_backtest_short_input(self, query, context):
        """Prépare l'input personnalisé pour le backtest SHORT"""
        chat_id = query.message.chat_id
        
        self.user_state[chat_id] = {
            'state': 'WAITING_BACKTEST_SHORT_HOURS',
            'menu_msg_id': query.message.message_id
        }
        
        await query.edit_message_text(
            text=get_custom_backtest_input_text(),
            parse_mode='Markdown'
        )
    
    async def _handle_toggle_rsi(self, query, context):
        """Active/désactive la stratégie RSI Bollinger"""
        db.toggle_strategy('rsi_bollinger')
        await self._handle_strategies_menu(query, context)
    
    async def _handle_strategy_rsi_info(self, query, context):
        """Affiche les informations de la stratégie RSI Bollinger"""
        await query.edit_message_text(
            text=get_strategy_rsi_info_text(),
            reply_markup=get_info_rsi_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_backtest_duration_rsi_menu(self, query, context):
        """Affiche le menu de sélection de durée pour RSI (en bougies 15min)"""
        await query.edit_message_text(
            text=get_backtest_duration_menu_text(),
            reply_markup=get_backtest_duration_rsi_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_custom_backtest_rsi_input(self, query, context):
        """Prépare l'input personnalisé pour le backtest RSI (bougies 15min)"""
        chat_id = query.message.chat_id
        
        self.user_state[chat_id] = {
            'state': 'WAITING_BACKTEST_RSI_CANDLES',
            'menu_msg_id': query.message.message_id
        }
        
        await query.edit_message_text(
            text="✍️ **BACKTEST RSI PERSONNALISÉ**\n\nEnvoyez le nombre de bougies 15min (ex: 5000).\n\n_Tapez autre chose pour annuler._",
            parse_mode='Markdown'
        )
    
    async def _handle_run_backtest_rsi(self, query, context, data: str):
        """
        Lance un backtest RSI avec une durée prédéfinie (en bougies 15min)
        
        Args:
            data: Callback data (format: btr_run_CANDLES)
        """
        try:
            candles = int(data.split('_')[2])
            chat_id = query.message.chat_id
            message_id = query.message.message_id
            
            async def update_status(text: str):
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode='Markdown'
                )
            
            report = await self.backtest_rsi_engine.run_backtest(candles, update_status)
            
            await query.edit_message_text(
                text=report,
                reply_markup=get_back_keyboard('menu_backtest_duration_rsi'),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest RSI : {e}", exc_info=True)
            await query.edit_message_text(
                text=f"❌ Erreur lors du backtest RSI : {str(e)}",
                reply_markup=get_back_keyboard('menu_backtest_duration_rsi'),
                parse_mode='Markdown'
            )
    
    async def _handle_history(self, query, context):
        """Affiche l'historique des performances"""
        db_data = db.load()
        
        await query.edit_message_text(
            text=get_history_text(db_data),
            reply_markup=get_back_keyboard('back_to_dash'),
            parse_mode='Markdown'
        )
    
    async def _handle_ask_stop(self, query, context):
        """Demande confirmation avant d'arrêter le bot"""
        await query.edit_message_text(
            text=get_confirm_stop_text(),
            reply_markup=get_confirm_stop_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_confirm_stop(self, query, context):
        """Arrête le bot après confirmation"""
        logger.warning("🛑 Arrêt du bot demandé par l'utilisateur")
        await query.message.delete()
        os._exit(0)
    
    async def handle_user_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gère les messages texte de l'utilisateur (pour input personnalisé).
        
        CORRECTION v8.3 : Vérification owner-only.
        
        Args:
            update: Update Telegram
            context: Context Telegram
        """
        chat_id = update.message.chat_id
        
        # CORRECTION v8.3 : vérification owner-only
        if chat_id != MY_CHAT_ID:
            logger.warning(f"Message non autorisé refusé (chat_id={chat_id})")
            return
        
        text = update.message.text
        
        # Supprimer le message de l'utilisateur
        try:
            await update.message.delete()
        except Exception:
            pass
        
        # Vérifier si on attend un input
        if chat_id not in self.user_state:
            return
        
        state = self.user_state[chat_id].get('state')
        
        if state == 'WAITING_BACKTEST_HOURS':
            await self._process_backtest_hours(chat_id, text, context)
        elif state == 'WAITING_BACKTEST_SHORT_HOURS':
            await self._process_backtest_short_hours(chat_id, text, context)
        elif state == 'WAITING_BACKTEST_RSI_CANDLES':
            await self._process_backtest_rsi_candles(chat_id, text, context)
        elif state.startswith('WAITING_BTM'):
            # Backtest Multi supprimé (Btc_Bot_V8) — on nettoie l'état résiduel
            if chat_id in self.user_state:
                del self.user_state[chat_id]
            await context.bot.send_message(
                chat_id=chat_id,
                text="ℹ️ **Backtest Multi retiré dans Btc_Bot_V8**",
                parse_mode='Markdown'
            )
    
    async def _process_backtest_hours(self, chat_id: int, text: str, context):
        """Traite l'input personnalisé pour backtest simple"""
        menu_msg_id = self.user_state[chat_id]['menu_msg_id']
        
        try:
            hours = int(text.strip())
            
            async def update_status(status_text: str):
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=status_text,
                    parse_mode='Markdown'
                )
            
            report = await self.backtest_engine.run_backtest(hours, update_status)
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_msg_id,
                text=report,
                reply_markup=get_back_keyboard('menu_backtest_duration'),
                parse_mode='Markdown'
            )
            
        except ValueError:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=get_invalid_number_text(),
                    reply_markup=get_back_keyboard('menu_backtest_duration')
                )
            except Exception:
                pass
        
        del self.user_state[chat_id]
    
    async def _process_backtest_short_hours(self, chat_id: int, text: str, context):
        """Traite l'input personnalisé pour backtest SHORT"""
        menu_msg_id = self.user_state[chat_id]['menu_msg_id']
        
        try:
            hours = int(text.strip())
            
            async def update_status(status_text: str):
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=status_text,
                    parse_mode='Markdown'
                )
            
            report = await self.backtest_short_engine.run_backtest(hours, update_status)
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_msg_id,
                text=report,
                reply_markup=get_back_keyboard('menu_backtest_duration_short'),
                parse_mode='Markdown'
            )
            
        except ValueError:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=get_invalid_number_text(),
                    reply_markup=get_back_keyboard('menu_backtest_duration_short')
                )
            except Exception:
                pass
        
        del self.user_state[chat_id]
    
    async def _process_backtest_rsi_candles(self, chat_id: int, text: str, context):
        """Traite l'input personnalisé pour backtest RSI"""
        menu_msg_id = self.user_state[chat_id]['menu_msg_id']
        
        try:
            candles = int(text.strip())
            
            async def update_status(status_text: str):
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=status_text,
                    parse_mode='Markdown'
                )
            
            report = await self.backtest_rsi_engine.run_backtest(candles, update_status)
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_msg_id,
                text=report,
                reply_markup=get_back_keyboard('menu_backtest_duration_rsi'),
                parse_mode='Markdown'
            )
            
        except ValueError:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=get_invalid_number_text(),
                    reply_markup=get_back_keyboard('menu_backtest_duration_rsi')
                )
            except Exception:
                pass
        
        del self.user_state[chat_id]


# Instance globale
callback_handler = CallbackHandler()
