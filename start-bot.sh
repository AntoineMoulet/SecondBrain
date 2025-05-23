#!/bin/bash

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg is not installed. Please install it before running the bot."
    echo "On macOS: brew install ffmpeg"
    echo "On Ubuntu/Debian: sudo apt install ffmpeg"
    exit 1
fi

echo "✅ ffmpeg is installed."

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping bot..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Source environment variables
echo "⚙️ Setting up environment..."
source .venv/bin/activate-env

# Start the bot
echo "🤖 Starting bot..."
python bot.py 