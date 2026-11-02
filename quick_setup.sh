#!/bin/bash

# Quick Setup Wizard for Flow Automation
# This script guides you through the 3 required manual steps

set -e

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Flow Automation - Quick Setup Wizard                  ║"
echo "║     3 steps to get you running!                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check 1: FFmpeg
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1/3: FFmpeg Installation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n1 | cut -d' ' -f3)
    echo -e "${GREEN}✓ FFmpeg is installed${NC} (version: $FFMPEG_VERSION)"
else
    echo -e "${RED}✗ FFmpeg is NOT installed${NC}"
    echo ""
    echo "To install FFmpeg, run:"
    echo -e "${YELLOW}brew install ffmpeg${NC}"
    echo ""
    read -p "Press Enter after installing FFmpeg, or Ctrl+C to exit..."
    
    if command -v ffmpeg &> /dev/null; then
        echo -e "${GREEN}✓ FFmpeg detected!${NC}"
    else
        echo -e "${RED}✗ FFmpeg still not found. Please install it first.${NC}"
        exit 1
    fi
fi

echo ""

# Check 2: LLM API Key
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2/3: LLM API Key Configuration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -f ".env" ]; then
    # Check for any API key
    if grep -qE "^(GEMINI|DEEPSEEK|OPENAI|ANTHROPIC)_API_KEY=.+" .env; then
        echo -e "${GREEN}✓ LLM API key(s) found in .env${NC}"
        echo ""
        echo "Configured providers:"
        grep -E "^(GEMINI|DEEPSEEK|OPENAI|ANTHROPIC)_API_KEY=.+" .env | while read line; do
            provider=$(echo "$line" | cut -d'_' -f1)
            echo "  • $provider"
        done
    else
        echo -e "${RED}✗ No LLM API keys found in .env${NC}"
        echo ""
        echo "You need to add at least ONE API key to .env file."
        echo ""
        echo -e "${YELLOW}Pick ONE (easiest first):${NC}"
        echo ""
        echo "1. Gemini (FREE, no credit card needed) ⭐ RECOMMENDED"
        echo "   Get key: https://makersuite.google.com/app/apikey"
        echo "   Add to .env: GEMINI_API_KEY=your-key-here"
        echo ""
        echo "2. DeepSeek (CHEAPEST: \$0.14 per 1M tokens)"
        echo "   Sign up: https://platform.deepseek.com"
        echo "   Add to .env: DEEPSEEK_API_KEY=your-key-here"
        echo ""
        echo "3. OpenAI (Most reliable, requires payment)"
        echo "   Get key: https://platform.openai.com/api-keys"
        echo "   Add to .env: OPENAI_API_KEY=your-key-here"
        echo ""
        read -p "Press Enter after adding your API key to .env, or Ctrl+C to exit..."
        
        if grep -qE "^(GEMINI|DEEPSEEK|OPENAI|ANTHROPIC)_API_KEY=.+" .env; then
            echo -e "${GREEN}✓ API key detected!${NC}"
        else
            echo -e "${RED}✗ No API key found. Please add one to .env${NC}"
            exit 1
        fi
    fi
else
    echo -e "${RED}✗ .env file not found${NC}"
    echo ""
    echo "Creating .env from template..."
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env and add your API key${NC}"
    echo ""
    echo "Run this command:"
    echo -e "${YELLOW}nano .env${NC}"
    echo ""
    echo "Then add ONE of these:"
    echo "  GEMINI_API_KEY=your-key-here"
    echo "  DEEPSEEK_API_KEY=your-key-here"
    echo "  OPENAI_API_KEY=your-key-here"
    echo ""
    exit 1
fi

echo ""

# Check 3: Selectors
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 3/3: Flow UI Selectors${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -f "selectors.yaml" ]; then
    echo -e "${GREEN}✓ selectors.yaml exists${NC}"
    echo ""
    echo -e "${YELLOW}IMPORTANT:${NC} You should verify these selectors work with the current Flow UI."
    echo ""
    echo "To verify selectors:"
    echo "1. Open Flow: https://labs.google/flow"
    echo "2. Open DevTools: Cmd + Option + I"
    echo "3. Enable Element Picker: Cmd + Shift + C"
    echo "4. Click each element (prompt box, generate button, etc.)"
    echo "5. Copy selector: Right-click → Copy → Copy selector"
    echo "6. Update selectors.yaml with correct selectors"
    echo ""
    read -p "Have you verified the selectors? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${YELLOW}TIP:${NC} You can run the automation first. If it fails with 'element not found',"
        echo "then come back and update the selectors."
    fi
else
    echo -e "${RED}✗ selectors.yaml not found${NC}"
    echo "This shouldn't happen. Please check your installation."
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "You're ready to run the automation! 🚀"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Create a test job:"
echo -e "   ${YELLOW}python scripts/test_single_job.py${NC}"
echo ""
echo "2. Run the automation:"
echo -e "   ${YELLOW}python scripts/run_automation.py${NC}"
echo ""
echo "3. Monitor with dashboard (optional):"
echo -e "   ${YELLOW}./dashboard.sh${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
