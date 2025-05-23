#!/bin/bash

echo "🔍 Testing SecondBrain Bot setup..."

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg is not installed. Please install it before running the bot."
    echo "On macOS: brew install ffmpeg"
    echo "On Ubuntu/Debian: sudo apt install ffmpeg"
    exit 1
fi

echo "✅ ffmpeg is installed."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✅ Python 3 is installed"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi
echo "✅ Virtual environment is ready"

# Check if activate-env exists in venv
if [ ! -f ".venv/bin/activate-env" ]; then
    echo "❌ activate-env file not found in .venv/bin/"
    exit 1
fi
echo "✅ activate-env file found"

# Source the environment variables
source .venv/bin/activate-env

# Check required environment variables
required_vars=("TG_TOKEN" "NOTION_TOKEN" "NOTION_DB_ID")
missing_vars=0

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing ${var} in activate-env"
        missing_vars=1
    fi
done

if [ $missing_vars -eq 1 ]; then
    exit 1
fi
echo "✅ Environment variables are set"

# Try to start the bot
echo "🚀 Attempting to start the bot..."
python3 bot.py &
BOT_PID=$!

# Wait a few seconds to see if the bot starts successfully
sleep 5

# Check if the bot process is still running
if ps -p $BOT_PID > /dev/null; then
    echo "✅ Bot started successfully!"
    echo "📝 Bot is running with PID: $BOT_PID"
    echo "💡 To stop the bot, run: kill $BOT_PID"
else
    echo "❌ Bot failed to start"
    exit 1
fi 