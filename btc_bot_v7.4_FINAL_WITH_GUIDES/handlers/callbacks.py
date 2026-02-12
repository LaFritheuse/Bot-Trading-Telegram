"""
Gestion des callbacks des boutons Telegram - Version Multi-StratÃ©gies
"""
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from database import db
from backtest import BacktestEngine
from backtest_short import BacktestShortEngine
from backtest_multi import BacktestMultiEngine
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
    get_confirm_stop_keyboard,
    get_backtest_multi_selection_keyboard,
    get_backtest_multi_mode_keyboard,
    get_backtest_multi_duration_keyboard
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
    get_invalid_number_text,
    get_backtest_multi_selection_text,
    get_backtest_multi_mode_text,
    get_backtest_multi_duration_text
)

logger = logging.getLogger(__name__)


class CallbackHandler:
    """Gestionnaire des callbacks Telegram"""
    
    def __init__(self):
        self.backtest_engine = BacktestEngine()
        self.backtest_short_engine = BacktestShortEngine()
        self.backtest_multi_engine = BacktestMultiEngine()
        self.user_state = {}  # Stockage temporaire pour inputs personnalisÃ©s
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Routeur principal des callbacks
        
        Args:
            update: Update Telegram
            context: Context Telegram
        """
        query = update.callback_query
        await query.answer()
        
        data = query.data
        chat_id = query.message.chat_id
        
        # Nettoyage de l'Ã©tat utilisateur (sauf pour les inputs custom et backtest multi)
        btm_callbacks = ['btm_toggle_sniper', 'btm_toggle_short', 'btm_next', 'btm_mode_seq', 'btm_mode_par', 'btm_custom_input']
        if data not in ['bt_custom_input', 'bts_custom_input', 'btm_custom_input'] + btm_callbacks:
            if chat_id in self.user_state:
                state = self.user_state[chat_id].get('state', '')
                # Ne pas effacer les Ã©tats du backtest multi
                if not state.startswith('WAITING_BTM'):
                    del self.user_state[chat_id]
        
        logger.info(f"Callback reÃ§u : {data} de l'utilisateur {chat_id}")
        
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
            # Backtest Multi
            'menu_backtest_multi': self._handle_backtest_multi_menu,
            'btm_toggle_sniper': self._handle_btm_toggle_sniper,
            'btm_toggle_short': self._handle_btm_toggle_short,
            'btm_toggle_rsi': self._handle_btm_toggle_rsi,
            'btm_next': self._handle_btm_next,
            'btm_select_mode': self._handle_btm_select_mode,
            'btm_mode_seq': self._handle_btm_mode_sequential,
            'btm_mode_par': self._handle_btm_mode_parallel,
            'btm_custom_input': self._handle_btm_custom_input
        }
        
        # Callbacks avec prÃ©fixes
        if data.startswith('bt_run_'):
            await self._handle_run_backtest(query, context, data)
        elif data.startswith('bts_run_'):
            await self._handle_run_backtest_short(query, context, data)
        elif data.startswith('btm_run_'):
            await self._handle_run_backtest_multi(query, context, data)
        elif data in handlers:
            await handlers[data](query, context)
        else:
            logger.warning(f"Callback non gÃ©rÃ© : {data}")
    
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
        """Affiche le menu des stratÃ©gies"""
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
        """Active/dÃ©sactive la stratÃ©gie Sniper LONG"""
        db.toggle_strategy('sniper_ema')
        await self._handle_strategies_menu(query, context)
    
    async def _handle_toggle_short(self, query, context):
        """Active/dÃ©sactive la stratÃ©gie Sniper SHORT"""
        db.toggle_strategy('sniper_short')
        await self._handle_strategies_menu(query, context)
    
    async def _handle_strategy_info(self, query, context):
        """Affiche les informations de la stratÃ©gie LONG"""
        await query.edit_message_text(
            text=get_strategy_info_text(),
            reply_markup=get_info_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_strategy_short_info(self, query, context):
        """Affiche les informations de la stratÃ©gie SHORT"""
        await query.edit_message_text(
            text=get_strategy_short_info_text(),
            reply_markup=get_info_short_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_backtest_duration_menu(self, query, context):
        """Affiche le menu de sÃ©lection de durÃ©e pour LONG"""
        await query.edit_message_text(
            text=get_backtest_duration_menu_text(),
            reply_markup=get_backtest_duration_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_backtest_duration_short_menu(self, query, context):
        """Affiche le menu de sÃ©lection de durÃ©e pour SHORT"""
        await query.edit_message_text(
            text=get_backtest_duration_menu_text(),
            reply_markup=get_backtest_duration_short_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_run_backtest(self, query, context, data: str):
        """
        Lance un backtest avec une durÃ©e prÃ©dÃ©finie
        
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
                text=f"âŒ Erreur lors du backtest : {str(e)}",
                reply_markup=get_back_keyboard('menu_backtest_duration'),
                parse_mode='Markdown'
            )
    
    async def _handle_custom_backtest_input(self, query, context):
        """PrÃ©pare l'input personnalisÃ© pour le backtest LONG"""
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
        Lance un backtest SHORT avec une durÃ©e prÃ©dÃ©finie
        
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
                text=f"âŒ Erreur lors du backtest SHORT : {str(e)}",
                reply_markup=get_back_keyboard('menu_backtest_duration_short'),
                parse_mode='Markdown'
            )
    
    async def _handle_custom_backtest_short_input(self, query, context):
        """PrÃ©pare l'input personnalisÃ© pour le backtest SHORT"""
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
    
    async def _handle_btm_toggle_rsi(self, query, context):
        """Toggle la sélection de RSI Bollinger pour backtest multi"""
        chat_id = query.message.chat_id
        
        if chat_id in self.user_state:
            current = self.user_state[chat_id].get('rsi_selected', False)
            self.user_state[chat_id]['rsi_selected'] = not current
            
            sniper_sel = self.user_state[chat_id]['sniper_selected']
            short_sel = self.user_state[chat_id]['short_selected']
            rsi_sel = self.user_state[chat_id]['rsi_selected']
            
            await query.edit_message_text(
                text=get_backtest_multi_selection_text(),
                reply_markup=get_backtest_multi_selection_keyboard(sniper_sel, short_sel, rsi_sel),
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
        """Demande confirmation avant d'arrÃªter le bot"""
        await query.edit_message_text(
            text=get_confirm_stop_text(),
            reply_markup=get_confirm_stop_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_confirm_stop(self, query, context):
        """ArrÃªte le bot aprÃ¨s confirmation"""
        logger.warning("ðŸ›‘ ArrÃªt du bot demandÃ© par l'utilisateur")
        await query.message.delete()
        os._exit(0)
    
    # ==================== BACKTEST MULTI ====================
    
    async def _handle_backtest_multi_menu(self, query, context):
        """Affiche le menu de sÃ©lection des stratÃ©gies pour backtest multi"""
        chat_id = query.message.chat_id
        
        # Initialiser l'Ã©tat avec les 2 stratÃ©gies sÃ©lectionnÃ©es par dÃ©faut
        self.user_state[chat_id] = {
            'state': 'WAITING_BTM_STRATEGIES',
            'sniper_selected': True,
            'short_selected': True
        }
        
        await query.edit_message_text(
            text=get_backtest_multi_selection_text(),
            reply_markup=get_backtest_multi_selection_keyboard(True, True),
            parse_mode='Markdown'
        )
    
    async def _handle_btm_toggle_sniper(self, query, context):
        """Toggle la sÃ©lection de Sniper LONG pour backtest multi"""
        chat_id = query.message.chat_id
        
        if chat_id in self.user_state:
            current = self.user_state[chat_id].get('sniper_selected', False)
            self.user_state[chat_id]['sniper_selected'] = not current
            
            sniper_sel = self.user_state[chat_id]['sniper_selected']
            short_sel = self.user_state[chat_id]['short_selected']
            
            await query.edit_message_text(
                text=get_backtest_multi_selection_text(),
                reply_markup=get_backtest_multi_selection_keyboard(sniper_sel, short_sel),
                parse_mode='Markdown'
            )
    
    async def _handle_btm_toggle_short(self, query, context):
        """Toggle la sÃ©lection de Sniper SHORT pour backtest multi"""
        chat_id = query.message.chat_id
        
        if chat_id in self.user_state:
            current = self.user_state[chat_id].get('short_selected', False)
            self.user_state[chat_id]['short_selected'] = not current
            
            sniper_sel = self.user_state[chat_id]['sniper_selected']
            short_sel = self.user_state[chat_id]['short_selected']
            
            await query.edit_message_text(
                text=get_backtest_multi_selection_text(),
                reply_markup=get_backtest_multi_selection_keyboard(sniper_sel, short_sel),
                parse_mode='Markdown'
            )
    
    async def _handle_btm_next(self, query, context):
        """Passe Ã  l'Ã©tape suivante : choix du mode"""
        chat_id = query.message.chat_id
        
        if chat_id not in self.user_state:
            await query.edit_message_text(
                text="âŒ Erreur d'Ã©tat. Retour au menu.",
                reply_markup=get_back_keyboard('menu_strategies')
            )
            return
        
        # VÃ©rifier qu'au moins une stratÃ©gie est sÃ©lectionnÃ©e
        sniper_sel = self.user_state[chat_id].get('sniper_selected', False)
        short_sel = self.user_state[chat_id].get('short_selected', False)
        
        if not sniper_sel and not short_sel:
            await query.answer("âš ï¸ SÃ©lectionne au moins une stratÃ©gie !", show_alert=True)
            return
        
        self.user_state[chat_id]['state'] = 'WAITING_BTM_MODE'
        
        await query.edit_message_text(
            text=get_backtest_multi_mode_text(),
            reply_markup=get_backtest_multi_mode_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_btm_select_mode(self, query, context):
        """Retour Ã  la sÃ©lection du mode"""
        await query.edit_message_text(
            text=get_backtest_multi_mode_text(),
            reply_markup=get_backtest_multi_mode_keyboard(),
            parse_mode='Markdown'
        )
    
    async def _handle_btm_mode_sequential(self, query, context):
        """Mode sÃ©quentiel sÃ©lectionnÃ©"""
        chat_id = query.message.chat_id
        
        if chat_id in self.user_state:
            self.user_state[chat_id]['mode'] = 'sequential'
            self.user_state[chat_id]['state'] = 'WAITING_BTM_DURATION'
            
            await query.edit_message_text(
                text=get_backtest_multi_duration_text(),
                reply_markup=get_backtest_multi_duration_keyboard(),
                parse_mode='Markdown'
            )
    
    async def _handle_btm_mode_parallel(self, query, context):
        """Mode parallÃ¨le sÃ©lectionnÃ©"""
        chat_id = query.message.chat_id
        
        if chat_id in self.user_state:
            self.user_state[chat_id]['mode'] = 'parallel'
            self.user_state[chat_id]['state'] = 'WAITING_BTM_DURATION'
            
            await query.edit_message_text(
                text=get_backtest_multi_duration_text(),
                reply_markup=get_backtest_multi_duration_keyboard(),
                parse_mode='Markdown'
            )
    
    async def _handle_run_backtest_multi(self, query, context, data: str):
        """Lance un backtest multi avec durÃ©e prÃ©dÃ©finie"""
        try:
            hours = int(data.split('_')[2])
            chat_id = query.message.chat_id
            message_id = query.message.message_id
            
            if chat_id not in self.user_state:
                await query.edit_message_text(
                    text="âŒ Erreur d'Ã©tat. Relance le backtest.",
                    reply_markup=get_back_keyboard('menu_strategies')
                )
                return
            
            # RÃ©cupÃ©rer les stratÃ©gies sÃ©lectionnÃ©es
            active_strategies = []
            if self.user_state[chat_id].get('sniper_selected'):
                active_strategies.append('sniper_ema')
            if self.user_state[chat_id].get('short_selected'):
                active_strategies.append('sniper_short')
            
            mode = self.user_state[chat_id].get('mode', 'sequential')
            
            async def update_status(text: str):
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode='Markdown'
                )
            
            report = await self.backtest_multi_engine.run_backtest(
                hours, 
                active_strategies,
                mode,
                update_status
            )
            
            await query.edit_message_text(
                text=report,
                reply_markup=get_back_keyboard('menu_strategies'),
                parse_mode='Markdown'
            )
            
            # Nettoyer l'Ã©tat
            del self.user_state[chat_id]
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest multi : {e}", exc_info=True)
            await query.edit_message_text(
                text=f"âŒ Erreur : {str(e)}",
                reply_markup=get_back_keyboard('menu_strategies'),
                parse_mode='Markdown'
            )
    
    async def _handle_btm_custom_input(self, query, context):
        """PrÃ©pare l'input personnalisÃ© pour backtest multi"""
        chat_id = query.message.chat_id
        
        if chat_id in self.user_state:
            self.user_state[chat_id]['state'] = 'WAITING_BTM_CUSTOM_HOURS'
            self.user_state[chat_id]['menu_msg_id'] = query.message.message_id
            
            await query.edit_message_text(
                text=get_custom_backtest_input_text(),
                parse_mode='Markdown'
            )
    
    async def handle_user_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        GÃ¨re les messages texte de l'utilisateur (pour input personnalisÃ©)
        
        Args:
            update: Update Telegram
            context: Context Telegram
        """
        chat_id = update.message.chat_id
        text = update.message.text
        
        # Supprimer le message de l'utilisateur
        try:
            await update.message.delete()
        except:
            pass
        
        # VÃ©rifier si on attend un input
        if chat_id not in self.user_state:
            return
        
        state = self.user_state[chat_id].get('state')
        
        if state == 'WAITING_BACKTEST_HOURS':
            await self._process_backtest_hours(chat_id, text, context)
        elif state == 'WAITING_BACKTEST_SHORT_HOURS':
            await self._process_backtest_short_hours(chat_id, text, context)
        elif state == 'WAITING_BACKTEST_RSI_CANDLES':
            await self._process_backtest_rsi_candles(chat_id, text, context)
        elif state == 'WAITING_BTM_CUSTOM_HOURS':
            await self._process_btm_custom_hours(chat_id, text, context)
    
    async def _process_backtest_hours(self, chat_id: int, text: str, context):
        """Traite l'input personnalisÃ© pour backtest simple"""
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
            except:
                pass
        
        del self.user_state[chat_id]
    
    async def _process_backtest_short_hours(self, chat_id: int, text: str, context):
        """Traite l'input personnalisÃ© pour backtest SHORT"""
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
            except:
                pass
        
        del self.user_state[chat_id]
    
    async def _process_btm_custom_hours(self, chat_id: int, text: str, context):
        """Traite l'input personnalisÃ© pour backtest multi"""
        menu_msg_id = self.user_state[chat_id]['menu_msg_id']
        
        try:
            hours = int(text.strip())
            
            active_strategies = []
            if self.user_state[chat_id].get('sniper_selected'):
                active_strategies.append('sniper_ema')
            if self.user_state[chat_id].get('short_selected'):
                active_strategies.append('sniper_short')
            if self.user_state[chat_id].get('rsi_selected'):
                active_strategies.append('rsi_bollinger')
            
            mode = self.user_state[chat_id].get('mode', 'sequential')
            
            async def update_status(status_text: str):
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=status_text,
                    parse_mode='Markdown'
                )
            
            report = await self.backtest_multi_engine.run_backtest(
                hours,
                active_strategies,
                mode,
                update_status
            )
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_msg_id,
                text=report,
                reply_markup=get_back_keyboard('menu_strategies'),
                parse_mode='Markdown'
            )
            
        except ValueError:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_msg_id,
                    text=get_invalid_number_text(),
                    reply_markup=get_back_keyboard('menu_strategies')
                )
            except:
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
            except:
                pass
        
        del self.user_state[chat_id]



# Instance globale
callback_handler = CallbackHandler()
