import os
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from notion_client import Client
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import logging
import whisper
import tempfile
import ffmpeg

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Whisper model
model = whisper.load_model("base")

async def transcribe_voice(voice_file_path: str) -> str:
    """
    Transcribe a voice message using Whisper.
    
    Args:
        voice_file_path: Path to the voice message file
        
    Returns:
        Transcribed text
    """
    try:
        # Transcribe the audio in French
        result = model.transcribe(voice_file_path, language="fr")
        return result["text"]
    except Exception as e:
        logger.error(f"Error transcribing voice message: {e}")
        raise

async def save_to_notion(text: str, ts: datetime, source: str = "text") -> None:
    """
    Save a message to Notion database.
    
    Args:
        text: The message text to save
        ts: The timestamp of the message
        source: The source of the message (text or voice)
    """
    notion = Client(auth=os.getenv("NOTION_TOKEN"))
    notion.pages.create(
        parent={"database_id": os.getenv("NOTION_DB_ID")},
        properties={
            "Message": {"title": [{"text": {"content": text}}]},
            "Date": {"date": {"start": ts.isoformat()}}
        }
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming voice messages.
    
    Args:
        update: The update object containing the voice message
        context: The context object for the bot
    """
    try:
        # Get the voice message
        voice = update.message.voice
        if not voice:
            return

        # Download the voice message
        voice_file = await context.bot.get_file(voice.file_id)
        
        # Create a temporary file for the voice message
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_voice:
            await voice_file.download_to_drive(temp_voice.name)
            
            # Transcribe the voice message
            transcribed_text = await transcribe_voice(temp_voice.name)
            
            # Save to Notion
            await save_to_notion(transcribed_text, update.message.date, "voice")
            
            # Send success response
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🎤 Transcrit: {transcribed_text}\n\n👌 Log sauvegardé"
            )
            
    except Exception as e:
        # Log the error
        logger.error(f"Error processing voice message: {e}")
        import traceback
        traceback.print_exc()
        
        # Send error response
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Échec de la transcription"
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
        await save_to_notion(content, ts, "text")
        
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
    
    # Add handlers
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    # Start polling
    logger.info("Starting bot in polling mode...")
    app.run_polling()

if __name__ == "__main__":
    main()