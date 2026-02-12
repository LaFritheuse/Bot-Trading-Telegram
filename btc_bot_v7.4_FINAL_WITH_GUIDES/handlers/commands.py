"""
Gestion des commandes Telegram
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db
from ui.keyboards import get_main_keyboard
from ui.messages import get_dashboard_text

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Commande /start - Affiche le dashboard principal
    
    Args:
        update: Update Telegram
        context: Context Telegram
    """
    try:
        # Supprimer le message de commande
        await update.message.delete()
    except:
        pass
    
    db_data = db.load()
    
    logger.info(f"Commande /start reÃ§ue de l'utilisateur {update.message.chat_id}")
    
    await update.message.reply_text(
        text=get_dashboard_text(db_data),
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )
