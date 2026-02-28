import os
import base64
import json
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import logging
import tempfile
import httpx
from notion_client import Client
from notion_client.errors import APIResponseError
from config import config
from llm_analyzer import analyzer
from telegram.ext import CommandHandler

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def transcribe_voice(voice_file_path: str) -> str:
    """Transcribe a voice message using OpenAI Whisper API."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=config.openai_api_key)
        with open(voice_file_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="fr"
            )
        return transcript.text
    except Exception as e:
        logger.error(f"Error transcribing voice message: {e}")
        raise

async def save_to_notion(text: str, ts: datetime, analysis_dict: dict) -> str:
    """
    Save a message to Notion database.

    Args:
        text: The message text to save
        ts: The timestamp of the message
        analysis_dict: Pre-computed analysis (topic, summary)

    Returns:
        The URL of the created Notion page
    """
    notion = Client(auth=config.notion_token)

    page_properties = {
        "Message": {"title": [{"text": {"content": text}}]},
        "Date": {"date": {"start": ts.isoformat()}},
        "Topic": {"rich_text": [{"text": {"content": analysis_dict.get("topic", "Unknown")}}]},
        "Summary": {"rich_text": [{"text": {"content": analysis_dict.get("summary", "No summary available")}}]},
    }

    logger.info(f"Creating Notion page with properties: {json.dumps(page_properties, indent=2)}")

    page_response = notion.pages.create(
        parent={"database_id": config.notion_database_id},
        properties=page_properties,
    )

    page_id = page_response.get("id") if isinstance(page_response, dict) else getattr(page_response, "id", None)
    if not page_id:
        raise ValueError(f"Notion page creation response missing 'id': {page_response}")

    page_url = (page_response.get("url") if isinstance(page_response, dict)
                else getattr(page_response, "url", None))
    logger.info(f"Notion page created: {page_id}")
    return page_url or f"https://notion.so/{page_id.replace('-', '')}"


async def save_to_vault(text: str, ts: datetime, analysis_dict: dict, source: str = "text") -> str:
    """
    Save a message to the Obsidian vault via GitHub API.

    Args:
        text: The message text to save
        ts: The timestamp of the message
        analysis_dict: Pre-computed analysis (topic, summary)
        source: The source of the message (text or voice)

    Returns:
        The GitHub URL of the created file
    """
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


async def save_capture(text: str, ts: datetime, source: str = "text") -> tuple[str, str]:
    """
    Analyze content once, then save to both Notion and vault.
    If either save fails, the error propagates (all or nothing).

    Returns:
        (notion_url, vault_url)
    """
    logger.info("Starting content analysis...")
    analysis_dict = await analyzer.analyze_content(text)
    logger.info(f"Analysis result: {analysis_dict}")

    notion_url = await save_to_notion(text, ts, analysis_dict)
    vault_url = await save_to_vault(text, ts, analysis_dict, source)

    return notion_url, vault_url


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages."""
    try:
        voice = update.message.voice
        if not voice:
            return

        voice_file = await context.bot.get_file(voice.file_id)

        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_voice:
            await voice_file.download_to_drive(temp_voice.name)
            transcribed_text = await transcribe_voice(temp_voice.name)
            notion_url, vault_url = await save_capture(transcribed_text, update.message.date, "voice")

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"🎤 Transcrit: {transcribed_text}\n\n"
                    f"👌 Sauvegardé: [Notion]({notion_url}) · [GitHub]({vault_url})"
                ),
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        import traceback
        traceback.print_exc()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Échec de la transcription"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming Telegram messages."""
    if not update.message or not update.message.text:
        return

    try:
        content = update.message.text
        ts = update.message.date

        logger.info(f"Processing message: {content[:50]}...")

        notion_url, vault_url = await save_capture(content, ts, "text")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"👌 Sauvegardé: [Notion]({notion_url}) · [GitHub]({vault_url})",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.error("Full error details:", exc_info=True)
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
        app = ApplicationBuilder().token(config.telegram_token).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT, handle_message))
        app.add_handler(MessageHandler(filters.VOICE, handle_voice))

        logger.info(f"Starting bot in {'production' if config.is_production else 'development'} mode...")
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        logger.error("Full error details:", exc_info=True)
        raise

if __name__ == "__main__":
    main()
