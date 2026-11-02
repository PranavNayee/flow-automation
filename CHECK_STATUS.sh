#!/bin/bash
# Check what's done and what needs to be done

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Flow Automation - Setup Status Check            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

# Check Python
echo "🐍 Python & Dependencies"
echo "─────────────────────────"
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    if ./venv/bin/python -c "import playwright, streamlit, yaml" 2>/dev/null; then
        echo "✅ Core packages installed"
    else
        echo "❌ Some packages missing"
    fi
else
    echo "❌ Virtual environment missing"
fi
echo ""

# Check database
echo "🗄️  Database"
echo "─────────────────────────"
if [ -f "data/queue.db" ]; then
    echo "✅ Database exists"
    TABLES=$(sqlite3 data/queue.db "SELECT name FROM sqlite_master WHERE type='table';" 2>/dev/null)
    if echo "$TABLES" | grep -q "checkpoints"; then
        echo "✅ Checkpoints table created"
    else
        echo "❌ Checkpoints table missing"
    fi
else
    echo "❌ Database not initialized"
fi
echo ""

# Check FFmpeg
echo "🎬 FFmpeg"
echo "─────────────────────────"
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg installed"
    ffmpeg -version 2>&1 | head -1
else
    echo "❌ FFmpeg NOT installed"
    echo "   → Run: brew install ffmpeg"
fi
echo ""

# Check .env
echo "⚙️  Configuration"
echo "─────────────────────────"
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    
    if grep -E "^(OPENAI|ANTHROPIC|GEMINI|DEEPSEEK)_API_KEY=.+" .env > /dev/null; then
        echo "✅ LLM API key configured"
    else
        echo "❌ NO LLM API key found"
        echo "   → Edit .env and add one of:"
        echo "      GEMINI_API_KEY=xxx (free tier)"
        echo "      DEEPSEEK_API_KEY=xxx (cheapest)"
        echo "      OPENAI_API_KEY=xxx (reliable)"
    fi
    
    if grep -E "^NOTIFICATION_WEBHOOK_URL=.+" .env > /dev/null; then
        echo "✅ Notifications configured"
    else
        echo "ℹ️  Notifications not configured (optional)"
    fi
else
    echo "❌ .env file NOT found"
    echo "   → Run: cp .env.example .env"
    echo "   → Then edit .env and add API keys"
fi
echo ""

# Check selectors
echo "🎯 Flow Selectors"
echo "─────────────────────────"
if [ -f "selectors.yaml" ]; then
    echo "✅ selectors.yaml exists"
    echo "⚠️  VERIFY selectors match current Flow UI"
    echo "   → Open https://labs.google/flow"
    echo "   → Use DevTools to check selectors"
else
    echo "❌ selectors.yaml missing"
fi
echo ""

echo "════════════════════════════════════════════════════════════"
echo "📋 TODO CHECKLIST"
echo "════════════════════════════════════════════════════════════"
echo ""

# TODO checklist
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ 1. Install FFmpeg: brew install ffmpeg"
else
    echo "✅ 1. FFmpeg installed"
fi

if [ -f ".env" ] && grep -E "^(OPENAI|ANTHROPIC|GEMINI|DEEPSEEK)_API_KEY=.+" .env > /dev/null; then
    echo "✅ 2. LLM API key configured"
else
    echo "❌ 2. Add LLM API key to .env"
fi

echo "⚠️  3. Verify selectors.yaml matches Flow UI"
echo "      (Open Flow + DevTools to check)"
echo ""

if command -v ffmpeg &> /dev/null && [ -f ".env" ] && grep -E "^(OPENAI|ANTHROPIC|GEMINI|DEEPSEEK)_API_KEY=.+" .env > /dev/null; then
    echo "════════════════════════════════════════════════════════════"
    echo "🎉 ALMOST READY!"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Just verify selectors, then run:"
    echo "  source venv/bin/activate"
    echo "  python scripts/test_single_job.py"
    echo "  python scripts/run_automation.py"
else
    echo "════════════════════════════════════════════════════════════"
    echo "⚠️  SETUP INCOMPLETE"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Complete the TODO items above, then test."
fi
echo ""
