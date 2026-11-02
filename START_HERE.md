# 🎯 START HERE - Your Action Items

## ✅ Already Done For You

I've completed all the automated setup:
- ✅ Virtual environment created (`venv/`)
- ✅ All Python packages installed
- ✅ Playwright Chromium browser installed
- ✅ Database initialized (`data/queue.db`)
- ✅ All directories created
- ✅ `.env` file created from template
- ✅ All scripts are executable

---

## ⚠️ YOU MUST DO THESE 3 THINGS

### 1. Install FFmpeg (5 minutes)

FFmpeg is required for video editing but must be installed system-wide.

**On macOS (you're on macOS):**
```bash
brew install ffmpeg
```

**Verify it worked:**
```bash
ffmpeg -version
```

---

### 2. Update Flow UI Selectors (15 minutes) ⚠️ CRITICAL!

Flow's UI changes frequently. You MUST inspect it and update the selectors.

**Step-by-step:**

```bash
# 1. Open Flow in your browser
open https://labs.google/flow

# 2. Open DevTools
# Press: Cmd + Option + I

# 3. Click the "Element Picker" icon (top-left of DevTools)
# Or press: Cmd + Shift + C

# 4. For each element below, click it and copy its selector:
```

**Elements you need to find:**

| Element | What to Look For | Where to Update |
|---------|------------------|-----------------|
| **Prompt textarea** | The text box where you type your prompt | `selectors.yaml` → `main.prompt_textarea` |
| **Generate button** | The button that creates the video | `selectors.yaml` → `main.prompt_submit_button` |
| **Loading indicator** | The spinner/loader while generating | `selectors.yaml` → `main.generating_indicator` |
| **Complete indicator** | Shows when generation is done | `selectors.yaml` → `main.generation_complete` |
| **Download button** | Button to download the video | `selectors.yaml` → `main.download_button` |
| **Video element** | The `<video>` tag showing the result | `selectors.yaml` → `main.video_preview` |

**How to copy a selector:**
1. Click the element with Element Picker active
2. DevTools highlights it in the Elements tab
3. Right-click the highlighted element
4. Select "Copy" → "Copy selector"
5. Paste into `selectors.yaml`

**Example - What you'll see:**
```
Before: prompt_textarea: 'textarea[placeholder*="prompt" i]'
After:  prompt_textarea: 'textarea[data-testid="prompt-input"]'
```

**Selector tips:**
- ✅ PREFER: `[data-testid="..."]`, `[aria-label="..."]`, `#id`
- ❌ AVOID: `.css-hash-12345` (these change often)
- Test in Console: `document.querySelector("your-selector")`

**When done:**
- Update the "Last verified" date at the top of `selectors.yaml`
- Save the file

---

### 3. Configure Rate Limits (2 minutes)

Edit `.env` file and set your limits:

```bash
cd /Users/pranavdipakbhainayee/Documents/youtube/flow-automation
nano .env
```

**Required settings (already have defaults, but review them):**

```env
# START CONSERVATIVE! (most important)
MAX_GENERATIONS_PER_HOUR=5
MAX_GENERATIONS_PER_DAY=20

# Delays between generations (seconds)
MIN_DELAY_BETWEEN_GENERATIONS=60
MAX_DELAY_BETWEEN_GENERATIONS=180

# Optional: Add your OpenAI key if you want LLM script generation
# OPENAI_API_KEY=sk-your-key-here

# Optional: Set your monthly Flow credit limit
# MONTHLY_CREDIT_LIMIT=100
```

**Save and exit:** Ctrl+X, then Y, then Enter

---

## 🧪 Testing (5 minutes)

Once you've done the 3 things above, test it:

```bash
cd /Users/pranavdipakbhainayee/Documents/youtube/flow-automation

# Activate virtual environment
source venv/bin/activate

# Create a test job
python scripts/test_single_job.py

# Run automation (browser will open)
python scripts/run_automation.py
```

**What will happen:**
1. Browser opens (Chrome/Chromium)
2. If not logged in → You'll be prompted to log in manually
3. Health check validates your selectors
4. Automation generates 1 test video
5. Video downloads to `./data/downloads/test_01.mp4`

**Watch closely!** This first run shows you if selectors are correct.

---

## 📊 Monitor with Dashboard (Optional)

In a **separate terminal**:

```bash
cd /Users/pranavdipakbhainayee/Documents/youtube/flow-automation
source venv/bin/activate
streamlit run src/dashboard.py
```

Opens at: http://localhost:8501

---

## 🚨 If Something Breaks

### "Element not found" error
→ Your selectors in `selectors.yaml` are wrong
→ Check the auto-generated `SELECTOR_UPDATE_GUIDE.md`
→ Re-inspect Flow UI and update selectors

### CAPTCHA appears
→ **GOOD!** The tool detected it and stopped (safety working)
→ Lower your rate limits in `.env`
→ Wait a few hours before trying again

### "FFmpeg not found"
→ Install FFmpeg: `brew install ffmpeg`
→ Verify: `ffmpeg -version`

### Can't log in to Flow
→ Make sure you're using a **separate Google account**
→ Not your primary account (risk of suspension)

---

## 📝 Full Workflow (After Setup)

### For Real Use:

```bash
# 1. Prepare your prompts (CSV or JSON)
nano my_prompts.csv
# Format:
# scene_id,prompt,aspect_ratio,duration
# scene_01,"A mountain at sunrise...",16:9,5

# 2. Import prompts
source venv/bin/activate
python scripts/import_prompts.py my_prompts.csv

# 3. Run automation
python scripts/run_automation.py

# 4. Monitor (separate terminal)
streamlit run src/dashboard.py

# 5. Videos download to ./data/downloads/
```

---

## 📚 Documentation

- **QUICKSTART.md** - 15-minute setup guide
- **README.md** - Complete 400+ line reference
- **FINAL_CHECKLIST.md** - Pre-flight checklist
- **flow-automation-SUMMARY.md** - Complete feature overview

---

## ⚠️ Critical Reminders

1. **Use a separate Google account** (NOT your primary!)
2. **Update selectors FIRST** (Flow UI changes often)
3. **Start with low rate limits** (5/hour is safe)
4. **Monitor the first 3-5 generations** (don't leave unattended)
5. **Stop immediately on warnings** (create `touch EMERGENCY_STOP`)

---

## 🎬 You're Almost Ready!

**Current Status:**
- ✅ All code installed
- ✅ Database initialized
- ✅ Environment configured
- ⏳ FFmpeg needs manual install
- ⏳ Selectors need updating
- ⏳ Rate limits need review

**Next:** Complete the 3 action items above, then test!

---

## 🆘 Need Help?

Check logs:
```bash
tail -f logs/flow_automation.log
```

Check queue status:
```bash
sqlite3 data/queue.db "SELECT * FROM jobs;"
```

Emergency stop:
```bash
touch EMERGENCY_STOP
```

---

**Good luck! 🚀**
