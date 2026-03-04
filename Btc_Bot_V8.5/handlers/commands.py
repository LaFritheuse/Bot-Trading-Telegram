"""
Gestion des commandes Telegram
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import MY_CHAT_ID
from database import db
from ui.keyboards import get_main_keyboard
from ui.messages import get_dashboard_text

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Commande /start - Affiche le dashboard principal.
    
    CORRECTION v8.3 : Vérification owner-only.
    Sans cette vérification, n'importe qui connaissant le lien du bot
    pouvait accéder au dashboard, toggler les stratégies, lancer des
    backtests ou arrêter le bot.
    
    Args:
        update: Update Telegram
        context: Context Telegram
    """
    # Vérification : seul le propriétaire peut interagir
    if update.message.chat_id != MY_CHAT_ID:
        logger.warning(f"Accès non autorisé refusé (chat_id={update.message.chat_id})")
        return
    
    try:
        # Supprimer le message de commande
        await update.message.delete()
    except Exception:
        pass
    
    db_data = db.load()
    
    logger.info(f"Commande /start reçue de l'utilisateur {update.message.chat_id}")
    
    await update.message.reply_text(
        text=get_dashboard_text(db_data),
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )
