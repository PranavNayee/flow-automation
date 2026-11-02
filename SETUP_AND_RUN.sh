#!/bin/bash
# Quick setup and run script

set -e

echo "🎬 Flow Automation - Quick Setup & Run"
echo "======================================"
echo ""

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate venv
source venv/bin/activate

echo "1️⃣  Checking dependencies..."
if ! python -c "import playwright" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    playwright install chromium
else
    echo "✅ Dependencies installed"
fi

echo ""
echo "2️⃣  Checking configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys"
    echo "Then run this script again"
    exit 0
fi

# Check if at least one LLM is configured
if ! grep -E "^(OPENAI|ANTHROPIC|GEMINI|DEEPSEEK)_API_KEY=.+" .env > /dev/null; then
    echo "⚠️  No LLM API key configured in .env"
    echo "Please add at least one:"
    echo "  - GEMINI_API_KEY (free tier available)"
    echo "  - DEEPSEEK_API_KEY (cheapest)"
    echo "  - OPENAI_API_KEY (reliable)"
    exit 1
fi

echo "✅ Configuration found"

echo ""
echo "3️⃣  Initializing database..."
if [ ! -f "data/queue.db" ]; then
    python scripts/init_db.py
else
    echo "✅ Database exists"
fi

echo ""
echo "4️⃣  Checking for jobs..."
JOB_COUNT=$(sqlite3 data/queue.db "SELECT COUNT(*) FROM jobs WHERE status='pending';" 2>/dev/null || echo "0")

if [ "$JOB_COUNT" = "0" ]; then
    echo "⚠️  No pending jobs in queue"
    echo ""
    echo "Create a test job? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        python scripts/test_single_job.py
    else
        echo "Import prompts with:"
        echo "  python scripts/import_prompts.py your_prompts.csv"
        exit 0
    fi
else
    echo "✅ Found $JOB_COUNT pending job(s)"
fi

echo ""
echo "5️⃣  Testing notification system..."
if grep -E "^NOTIFICATION_WEBHOOK_URL=.+" .env > /dev/null; then
    echo "📱 Webhook configured, testing..."
    python -c "from src.notifications import NotificationService; from src.utils import Config; NotificationService(Config().get_env('NOTIFICATION_WEBHOOK_URL')).test_notification()" 2>/dev/null && echo "✅ Notifications working" || echo "⚠️  Notification test failed (optional)"
else
    echo "ℹ️  No webhook configured (optional feature)"
fi

echo ""
echo "======================================"
echo "🚀 Ready to run!"
echo "======================================"
echo ""
echo "Starting automation in 3 seconds..."
echo "Press Ctrl+C to cancel"
sleep 3

python scripts/run_automation.py
