#!/bin/bash

# Validate Setup - Quick health check before running automation
# Run this after completing YOUR_TODO.md steps

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Flow Automation - Setup Validator                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ISSUES=0

# Check 1: FFmpeg
echo -n "Checking FFmpeg... "
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ NOT INSTALLED${NC}"
    echo "  → Run: brew install ffmpeg"
    ISSUES=$((ISSUES + 1))
fi

# Check 2: Virtual environment
echo -n "Checking Python venv... "
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ NOT FOUND${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check 3: .env file
echo -n "Checking .env file... "
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC}"
    
    # Check for API keys
    echo -n "  Checking LLM API keys... "
    if grep -qE "^(GEMINI|DEEPSEEK|OPENAI|ANTHROPIC)_API_KEY=.+[^your-key-here]" .env; then
        echo -e "${GREEN}✓${NC}"
        grep -E "^(GEMINI|DEEPSEEK|OPENAI|ANTHROPIC)_API_KEY=.+" .env | while read line; do
            provider=$(echo "$line" | cut -d'_' -f1)
            # Check if it's not the placeholder
            if ! echo "$line" | grep -q "your-key-here"; then
                echo "    • $provider configured"
            fi
        done
    else
        echo -e "${RED}✗ NO KEYS FOUND${NC}"
        echo "  → Add at least one API key to .env"
        echo "  → Options: GEMINI_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY"
        ISSUES=$((ISSUES + 1))
    fi
else
    echo -e "${RED}✗ NOT FOUND${NC}"
    echo "  → Copy .env.example to .env and add your API keys"
    ISSUES=$((ISSUES + 1))
fi

# Check 4: Database
echo -n "Checking database... "
if [ -f "data/queue.db" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ NOT INITIALIZED${NC}"
    echo "  → Will be created on first run"
fi

# Check 5: Playwright
echo -n "Checking Playwright browsers... "
if [ -d "$HOME/Library/Caches/ms-playwright" ] || [ -d "venv/lib/python*/site-packages/playwright" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ MAY NEED INSTALL${NC}"
    echo "  → Run: source venv/bin/activate && playwright install chromium"
fi

# Check 6: Required Python packages
echo -n "Checking Python packages... "
source venv/bin/activate 2>/dev/null
if python -c "import playwright; import openai; import yaml" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ MISSING PACKAGES${NC}"
    echo "  → Run: source venv/bin/activate && pip install -r requirements.txt"
    ISSUES=$((ISSUES + 1))
fi

# Check 7: selectors.yaml
echo -n "Checking selectors.yaml... "
if [ -f "selectors.yaml" ]; then
    echo -e "${GREEN}✓${NC}"
    echo -e "  ${YELLOW}⚠ Remember to verify these selectors match current Flow UI${NC}"
else
    echo -e "${RED}✗ NOT FOUND${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC} You're ready to run the automation."
    echo ""
    echo "Next steps:"
    echo "  1. Create test job: python scripts/test_single_job.py"
    echo "  2. Run automation: python scripts/run_automation.py"
    echo "  3. Monitor dashboard: ./dashboard.sh"
else
    echo -e "${RED}✗ Found $ISSUES issue(s)${NC}"
    echo ""
    echo "Fix the issues above, then run this script again."
    echo "See YOUR_TODO.md for detailed instructions."
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
