# Final Pre-Flight Checklist

Before you run the automation for the first time, complete these steps:

## ⚠️ CRITICAL: Read the Disclaimers

- [ ] I have read and understood that this may violate Google's Terms of Service
- [ ] I understand my account could be suspended or terminated
- [ ] I am using a separate Google account (not my primary account)
- [ ] I accept full responsibility for any consequences

## 🔧 Installation

- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Virtual environment created (`python3 -m venv venv`)
- [ ] Virtual environment activated (`source venv/bin/activate`)
- [ ] Requirements installed (`pip install -r requirements.txt`)
- [ ] Playwright browser installed (`playwright install chromium`)
- [ ] FFmpeg installed (`ffmpeg -version`)

## ⚙️ Configuration

- [ ] Copied `.env.example` to `.env`
- [ ] Set `MAX_GENERATIONS_PER_HOUR=5` (start conservative!)
- [ ] Set `MAX_GENERATIONS_PER_DAY=20` (start conservative!)
- [ ] Set `BROWSER_PROFILE_PATH=./playwright-state`
- [ ] (Optional) Set OpenAI/Anthropic API key for script generation
- [ ] (Optional) Monthly credit limit configured

## 🎯 Selector Verification (MOST IMPORTANT!)

- [ ] Opened https://labs.google/flow in browser
- [ ] Opened DevTools (F12 or Cmd+Opt+I)
- [ ] Found the prompt textarea element
- [ ] Copied its selector (right-click → Copy → Copy selector)
- [ ] Updated `selectors.yaml` → `main.prompt_textarea`
- [ ] Found the "Generate" button
- [ ] Updated `selectors.yaml` → `main.prompt_submit_button`
- [ ] Found the generating indicator (spinner/loading)
- [ ] Updated `selectors.yaml` → `main.generating_indicator`
- [ ] Found the completion indicator
- [ ] Updated `selectors.yaml` → `main.generation_complete`
- [ ] Found the download button or video element
- [ ] Updated `selectors.yaml` → `main.download_button` and `main.video_preview`
- [ ] Updated "Last verified" date at top of `selectors.yaml`

**Selector Tips:**
- Prefer: `[data-testid="..."]`, `[aria-label="..."]`, semantic HTML
- Avoid: `.css-class-123456` (changes frequently)
- Test in Console: `document.querySelector("your-selector")`

## 🗄️ Database Initialization

- [ ] Ran `python scripts/init_db.py`
- [ ] Verified `./data/` directory created
- [ ] Verified `./logs/` directory created
- [ ] Verified `queue.db` created (after init_db)

## 🧪 Test Run

- [ ] Created a single test job (`python scripts/test_single_job.py`)
- [ ] Ran automation (`python scripts/run_automation.py`)
- [ ] Browser opened successfully
- [ ] Logged in to Google account (if prompted)
- [ ] Health check passed ✓
- [ ] Watched the first generation complete
- [ ] Video downloaded to `./data/downloads/`
- [ ] No warnings or errors appeared
- [ ] Reviewed logs in `./logs/flow_automation.log`

## 📊 Monitoring Setup

- [ ] Tested dashboard: `streamlit run src/dashboard.py`
- [ ] Dashboard opens at http://localhost:8501
- [ ] Can see queue statistics
- [ ] Can view completed jobs

## 🛡️ Safety Measures Understood

- [ ] Know how to create `EMERGENCY_STOP` file (`touch EMERGENCY_STOP`)
- [ ] Reviewed rate limits in `.env` (start LOW!)
- [ ] Understand the tool stops on CAPTCHA/warnings
- [ ] Know that screenshots are saved on errors
- [ ] Understand the queue is resume-safe (can restart after crash)

## 📝 First Real Run Plan

- [ ] Prepared 5-10 prompts in CSV or JSON format
- [ ] Imported prompts: `python scripts/import_prompts.py prompts.csv`
- [ ] Verified queue: check dashboard or logs
- [ ] Plan to monitor the first 3-5 generations closely
- [ ] Will not leave unattended for the first session
- [ ] Have reviewed what to do if selectors break (update selectors.yaml)

## 🎬 Optional: Advanced Features

- [ ] (Optional) YouTube OAuth setup completed
- [ ] (Optional) LLM API key configured for script generation
- [ ] (Optional) Reviewed video editing examples in README
- [ ] (Optional) Prepared background music/subtitle files

## 🚨 Emergency Contacts

**If Flow UI Changes:**
1. Check auto-generated `SELECTOR_UPDATE_GUIDE.md`
2. Update `selectors.yaml`
3. Test with single job
4. See README → "Flow UI Changes" section

**If Account Warnings Appear:**
1. Stop immediately (create `EMERGENCY_STOP`)
2. Review logs for what triggered it
3. Lower rate limits in `.env`
4. Wait 24-48 hours before resuming

**If CAPTCHA Appears:**
1. Tool auto-stops (safety feature working!)
2. Complete CAPTCHA manually if needed
3. Lower rate limits significantly
4. Increase delays between generations

---

## ✅ Ready to Run

If you've checked ALL the boxes above, you're ready!

### Start Command

```bash
# Activate virtual environment
source venv/bin/activate

# Run automation
python scripts/run_automation.py

# In another terminal, start dashboard
streamlit run src/dashboard.py
```

### What to Watch For

✅ **Good Signs:**
- Health check passes
- Videos generate successfully
- Downloads complete without errors
- Logs show normal operation

⚠️ **Warning Signs:**
- "Element not found" errors → Update selectors
- CAPTCHA appears → Lower rate limits
- Warning messages → Stop and review
- Repeated failures → Check logs and selectors

### After First Session

- [ ] Reviewed all logs
- [ ] Checked downloaded videos
- [ ] No warnings or unusual activity
- [ ] Ready to scale up (cautiously!)

---

**Remember: Start slow, monitor closely, stop on any warnings!**

Good luck! 🎬
