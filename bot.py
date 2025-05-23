import os
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from notion_client import Client
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from notion_client import Client
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def save_to_notion(text: str, ts: datetime) -> None:
    """
    Save a message to Notion database.
    
    Args:
        text: The message text to save
        ts: The timestamp of the message
    """
    notion = Client(auth=os.getenv("NOTION_TOKEN"))
    notion.pages.create(
        parent={"database_id": os.getenv("NOTION_DB_ID")},
        properties={
            "Message": {"title": [{"text": {"content": text}}]},
            "Date": {"date": {"start": ts.isoformat()}}
        }
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming Telegram messages.
    
    Args:
        update: The update object containing the message
        context: The context object for the bot
    """
    # Ignore non-text messages
    if not update.message or not update.message.text:
        return
    
    try:
        # Extract message content and timestamp
        content = update.message.text
        ts = update.message.date
        
        # Save to Notion
        await save_to_notion(content, ts)
        
        # Send success response
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="👌 Log sauvegardé"
        )
        
    except Exception as e:
        # Log the error
        logger.error(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()
        
        # Send error response
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Échec"
        ) 

def main():
    # Get environment variables
    tg_token = os.getenv("TG_TOKEN")
    if not tg_token:
        raise ValueError("TG_TOKEN environment variable is not set")
    
    # Build application
    app = ApplicationBuilder().token(tg_token).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # Start polling
    logger.info("Starting bot in polling mode...")
    app.run_polling()

if __name__ == "__main__":
    main()