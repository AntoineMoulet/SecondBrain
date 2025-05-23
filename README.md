# Telegram to Notion Bot

A Telegram bot that automatically forwards messages to a Notion database, allowing you to easily save and organize your Telegram messages in Notion.

## Features

- Automatically saves incoming Telegram messages to a Notion database
- Preserves message timestamps
- Simple confirmation responses
- Error handling with user feedback

## Prerequisites

- Python 3.7 or higher
- A Telegram Bot Token (obtained from [@BotFather](https://t.me/botfather))
- A Notion API Token
- A Notion Database ID
- A public URL for webhook hosting

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
TG_TOKEN=your_telegram_bot_token
NOTION_TOKEN=your_notion_api_token
NOTION_DB_ID=your_notion_database_id
APP_URL=your_public_url
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install the required dependencies:
```bash
pip install python-telegram-bot notion-client python-dotenv
```

## Usage

1. Set up your environment variables as described above
2. Run the bot:
```bash
python bot.py
```

The bot will start listening for messages on port 8080 and will forward any text messages it receives to your Notion database.

## How it Works

1. The bot receives messages through a Telegram webhook
2. When a text message is received, it extracts the content and timestamp
3. The message is saved to your Notion database with:
   - Message content in the "Message" property
   - Timestamp in the "Date" property
4. The bot responds with a confirmation message (👌) or an error message (❌) if something goes wrong

## Notion Database Setup

Your Notion database should have the following properties:
- Message (Title type)
- Date (Date type)

## Error Handling

The bot includes error handling that will:
- Log errors to the console
- Send a failure message (❌) to the user if something goes wrong
- Print stack traces for debugging

## License

[Add your chosen license here]

## Contributing

[Add contribution guidelines if applicable] 