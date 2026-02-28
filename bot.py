import os
import base64
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import logging
import whisper
import tempfile
import ffmpeg
import httpx
from config import config
from llm_analyzer import analyzer
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

async def save_to_vault(text: str, ts: datetime, source: str = "text") -> str:
    """
    Save a message to the Obsidian vault via GitHub API.

    Args:
        text: The message text to save
        ts: The timestamp of the message
        source: The source of the message (text or voice)

    Returns:
        The GitHub URL of the created file
    """
    logger.info("Starting content analysis...")
    analysis_dict = await analyzer.analyze_content(text)
    logger.info(f"Analysis result: {analysis_dict}")

    topic_slug = analysis_dict.get("topic", "note").lower().replace(" ", "-")
    filename = ts.strftime("%Y-%m-%d-%H%M%S") + f"-{topic_slug}.md"

    file_content = f"""---
date: {ts.isoformat()}
type: {source}
topic: {analysis_dict.get("topic", "")}
summary: {analysis_dict.get("summary", "")}
---

{text}
"""
    path = f"vault/captures/{filename}"
    url = f"https://api.github.com/repos/{config.github_repo}/contents/{path}"

    async with httpx.AsyncClient() as client:
        response = await client.put(
            url,
            headers={
                "Authorization": f"token {config.github_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={
                "message": f"capture: {analysis_dict.get('topic', 'note')}",
                "content": base64.b64encode(file_content.encode()).decode()
            }
        )
        response.raise_for_status()

    logger.info(f"Saved capture to vault: {path}")
    return f"https://github.com/{config.github_repo}/blob/main/{path}"

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
            
            # Save to vault
            vault_url = await save_to_vault(transcribed_text, update.message.date, "voice")

            # Send success response
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🎤 Transcrit: {transcribed_text}\n\n[👌 Sauvegardé]({vault_url})",
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
        
        # Save to vault
        vault_url = await save_to_vault(content, ts, "text")

        # Send success response
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"[👌 Sauvegardé]({vault_url})",
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
    await update.message.reply_text('👋 Salut ! Je suis ton bot SecondBrain. Envoie-moi un message ou un vocal, je le sauvegarde dans ton vault.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🧠 *SecondBrain Bot*

Capture tes pensées directement dans ton vault Obsidian.

*Commandes :*
/start - Démarrer le bot
/help - Afficher cette aide

*Fonctionnalités :*
• Sauvegarde les messages texte dans vault/captures/
• Transcrit les messages vocaux (Whisper)
• Analyse IA du contenu (topic + résumé)
• Format Markdown avec métadonnées

Envoie n'importe quel message ou vocal !
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