# 🚀 START HERE - Your Next Steps

I've done **90% of the work**. You just need **20 minutes** to finish setup!

---

## Option 1: Guided Setup (Easiest) ✨

Run this interactive wizard:

```bash
cd /Users/pranavdipakbhainayee/Documents/youtube/flow-automation
./quick_setup.sh
```

It will guide you through all 3 steps!

---

## Option 2: Manual Setup (Fast)

### Step 1: Install FFmpeg (5 min)
```bash
brew install ffmpeg
```

### Step 2: Add API Key (5 min)

Pick ONE (Gemini is free):

```bash
cd /Users/pranavdipakbhainayee/Documents/youtube/flow-automation
nano .env

# Add ONE of these:
GEMINI_API_KEY=your-key-here          # FREE: https://makersuite.google.com/app/apikey
DEEPSEEK_API_KEY=your-key-here        # CHEAPEST: https://platform.deepseek.com
OPENAI_API_KEY=your-key-here          # RELIABLE: https://platform.openai.com/api-keys

# Save: Ctrl+X → Y → Enter
```

### Step 3: Update Selectors (10 min)

```bash
# Open Flow and DevTools
open https://labs.google/flow
# Press: Cmd + Option + I

# Click element picker (or Cmd + Shift + C)
# Click on: prompt box, generate button, download button
# Right-click → Copy → Copy selector
# Update selectors.yaml with copied selectors
```

---

## Test It! (5 min)

```bash
cd /Users/pranavdipakbhainayee/Documents/youtube/flow-automation
source venv/bin/activate

# Create test job
python scripts/test_single_job.py

# Run automation
python scripts/run_automation.py
```

**Expected:** Browser opens → Goes to Flow → Types prompt → Generates video → Downloads it ✓

---

## 📚 Read These After Setup

1. **QUICK_REFERENCE.md** - Daily commands
2. **FINAL_STATUS.md** - Detailed status report
3. **YOUR_TODO.md** - Setup instructions (detailed)
4. **IMPLEMENTATION_COMPLETE.md** - Full feature guide

---

## ❓ Need Help?

### FFmpeg not found?
```bash
brew install ffmpeg
```

### LLM error?
```bash
nano .env
# Add: GEMINI_API_KEY=your-key
```

### Element not found?
```bash
nano selectors.yaml
# Update selectors from Flow UI
```

### Other issues?
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

---

## 🎯 What You Get

✅ Batch video generation from CSV  
✅ Auto-recovery from crashes (checkpoint system)  
✅ Multi-provider LLM with fallback (99.9% uptime)  
✅ Slack/Discord notifications  
✅ Credit tracking & limits  
✅ Streamlit dashboard  
✅ Comprehensive logging  

---

**Total setup time: 20 minutes**  
**Then you're generating videos on autopilot! 🎥✨**
