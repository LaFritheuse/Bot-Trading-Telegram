"""
BTC Trader Bot V8 - Point d'entrée principal

Bot de trading Bitcoin avec stratégie Sniper EMA V11
Interface Telegram avec backtesting intégré
"""
import logging
import sys
from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Imports locaux
from config import (
    TOKEN,
    MY_CHAT_ID,
    MARKET_CHECK_INTERVAL,
    MARKET_CHECK_FIRST_RUN,
    validate_config
)
from database import db
from handlers.commands import cmd_start
from handlers.callbacks import callback_handler
from trading import trading_engine
from ui.keyboards import get_main_keyboard
from ui.messages import get_dashboard_text


async def post_startup(application):
    """
    Fonction appelée au démarrage du bot
    
    Configure les commandes et envoie le message initial
    
    Args:
        application: Application Telegram
    """
    logger.info("🚀 Démarrage du BTC Trader Bot V8...")
    
    # Retirer les commandes du menu (pour garder l'interface propre)
    await application.bot.set_my_commands([])
    
    # Charger la DB
    db_data = db.load()
    
    # Envoyer le dashboard initial
    await application.bot.send_message(
        chat_id=MY_CHAT_ID,
        text=get_dashboard_text(db_data),
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )
    
    logger.info("✅ Bot démarré avec succès")
    logger.info(f"💰 Balance actuel : {db_data['balance']:.2f}$")
    logger.info(f"📊 Total trades historique : {len(db_data.get('trades', []))}")


def main():
    """Point d'entrée principal"""
    
    # Validation de la configuration
    try:
        validate_config()
    except ValueError as e:
        logger.error(str(e))
        logger.error("Créez un fichier .env avec vos credentials (voir .env.example)")
        sys.exit(1)
    
    logger.info("Configuration validée ✓")
    
    # Construction de l'application
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_startup)
        .build()
    )
    
    # Enregistrement des handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CallbackQueryHandler(callback_handler.handle_callback))
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            callback_handler.handle_user_message
        )
    )
    
    # Job de vérification du marché
    application.job_queue.run_repeating(
        trading_engine.check_market,
        interval=MARKET_CHECK_INTERVAL,
        first=MARKET_CHECK_FIRST_RUN
    )
    
    logger.info(f"⏰ Scan de marché : toutes les {MARKET_CHECK_INTERVAL}s")
    
    # Démarrage du bot
    logger.info("🔄 Lancement du polling...")
    application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt du bot par l'utilisateur")
    except Exception as e:
        logger.critical(f"💥 Erreur critique : {e}", exc_info=True)
        sys.exit(1)
