# SecondBrain Bot

A Telegram bot that saves messages to a Notion database.

## Features

- Forward messages from Telegram to Notion
- Automatic timestamp tracking
- Simple and reliable

## Setup

1. Clone the repository:
```bash
git clone https://github.com/AntoineMoulet/SecondBrain.git
cd SecondBrain
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your credentials:
```
TG_TOKEN=your_telegram_bot_token
NOTION_TOKEN=your_notion_integration_token
NOTION_DB_ID=your_notion_database_id
```

4. Start the bot:
```bash
./start-bot.sh
```

## Usage

1. Start a chat with your bot on Telegram
2. Send any message
3. The message will be automatically saved to your Notion database

## Development

The bot is written in Python and uses:
- python-telegram-bot for Telegram integration
- notion-client for Notion API
- python-dotenv for environment management

## License

MIT 