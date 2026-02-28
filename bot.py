import os
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from notion_client import Client
from notion_client.errors import APIResponseError
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import logging
import whisper
import tempfile
import ffmpeg
from config import config
from llm_analyzer import analyzer
import json
from telegram.ext import CommandHandler

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

async def save_to_notion(text: str, ts: datetime, source: str = "text") -> str:
    """
    Save a message to Notion database.

    Args:
        text: The message text to save
        ts: The timestamp of the message
        source: The source of the message (text or voice)

    Returns:
        The URL of the created Notion page
    """
    try:
        logger.info("Starting content analysis...")
        # Analyze the content
        analysis_dict = await analyzer.analyze_content(text)
        logger.info(f"Analysis result: {analysis_dict}")
        
        # Create Notion client
        notion = Client(auth=config.notion_token)
        logger.info("Notion client created")
        
        # Prepare page properties
        page_properties = {
            "Message": {"title": [{"text": {"content": text}}] },
            "Date": {"date": {"start": ts.isoformat()} },
            "Topic": {"rich_text": [{"text": {"content": analysis_dict.get("topic", "Unknown")}}] },
            "Summary": {"rich_text": [{"text": {"content": analysis_dict.get("summary", "No summary available")}}] }
        }
        
        logger.info(f"Attempting to create page in Notion with properties: {json.dumps(page_properties, indent=2)}")
        
        # Create the page
        page_response = notion.pages.create(
            parent={"database_id": config.notion_database_id},
            properties=page_properties
        )
        
        logger.info(f"Raw response from Notion API (pages.create): {page_response}")

        page_id = None
        # Check if the response is a dictionary (observed behavior)
        if isinstance(page_response, dict):
            page_id = page_response.get("id")
        # Fallback: check if it's an object with an 'id' attribute (e.g., Pydantic model)
        elif hasattr(page_response, "id"):
            page_id = page_response.id
        
        if page_id:
            logger.info(f"Page successfully created in Notion with ID: {page_id}")
            page_url = page_response.get("url") if isinstance(page_response, dict) else getattr(page_response, "url", None)
            return page_url or f"https://notion.so/{page_id.replace('-', '')}"
        else:
            # This path means page creation failed to return an ID in any expected format.
            response_content = str(page_response)
            logger.error(f"Notion page creation response did not contain a usable 'id'. Response: {response_content}")
            raise ValueError(f"Failed to create page in Notion - response missing 'id' or in unexpected format. Notion API returned: {response_content}")
            
    except APIResponseError as e: # Specifically catch Notion API errors
        logger.error(f"Notion API Error during page creation: Status {e.status}, Code: {e.code}, Message: {e.message}")
        logger.error(f"Notion API Error Body: {e.body}")
        raise ValueError(f"Notion API Error: {e.message} (Status: {e.status}, Code: {e.code})") from e
    except Exception as e:
        logger.error(f"Unexpected error in save_to_notion: {str(e)}")
        logger.error("Full error details for save_to_notion:", exc_info=True)
        raise

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
            notion_url = await save_to_notion(transcribed_text, update.message.date, "voice")

            # Send success response
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🎤 Transcrit: {transcribed_text}\n\n[👌 Log sauvegardé]({notion_url})",
                parse_mode="Markdown"
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
        
        logger.info(f"Processing message: {content[:50]}...")
        
        # Save to Notion
        notion_url = await save_to_notion(content, ts, "text")

        # Send success response
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"[👌 Log sauvegardé]({notion_url})",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        # Log the error with full details
        logger.error(f"Error processing message: {str(e)}")
        logger.error("Full error details:", exc_info=True)
        
        # Send error response
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Échec: {str(e)}"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('👋 Hi! I\'m your SecondBrain bot. Send me any message and I\'ll save it to Notion with an AI analysis!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🤖 *SecondBrain Bot Help*

I can help you save and analyze your messages in Notion:

*Commands:*
/start - Start the bot
/help - Show this help message

*Features:*
• Save text messages to Notion
• Transcribe voice messages
• AI analysis of content
• Automatic topic and summary generation

Just send me any message or voice note!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    try:
        # Build application using config
        app = ApplicationBuilder().token(config.telegram_token).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT, handle_message))
        app.add_handler(MessageHandler(filters.VOICE, handle_voice))
        
        # Start polling with specific parameters
        logger.info(f"Starting bot in {'production' if config.is_production else 'development'} mode...")
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # This will ignore any pending updates
            close_loop=False
        )
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        logger.error("Full error details:", exc_info=True)
        raise

if __name__ == "__main__":
    main()