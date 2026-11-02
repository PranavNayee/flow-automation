# Quick Start Guide

Get up and running in 15 minutes.

## 1. Install Dependencies (5 min)

```bash
cd flow-automation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Install FFmpeg
brew install ffmpeg  # macOS
# sudo apt install ffmpeg  # Linux
```

## 2. Configure (5 min)

```bash
# Copy environment template
cp .env.example .env

# Edit .env - IMPORTANT!
nano .env
```

**Minimum required settings:**
```env
MAX_GENERATIONS_PER_HOUR=5
MAX_GENERATIONS_PER_DAY=20
BROWSER_PROFILE_PATH=./playwright-state
```

**Update Flow selectors:**
1. Open https://labs.google/flow in your browser
2. Open DevTools (F12)
3. Verify these selectors work:
   - Prompt textarea
   - Generate button
4. Update `selectors.yaml` if needed

## 3. Initialize (2 min)

```bash
# Create database and directories
python scripts/init_db.py
```

## 4. Test with One Job (3 min)

Create a test job:

```bash
cat > test.csv << EOF
scene_id,prompt,aspect_ratio,duration
test_01,"A peaceful mountain lake at sunrise, golden light reflecting on calm water, cinematic wide shot",16:9,5
EOF

# Import test job
python scripts/import_prompts.py test.csv

# Run automation
python scripts/run_automation.py
```

**What happens:**
1. Browser opens
2. If not logged in, you'll be prompted to log in manually
3. Health check validates selectors
4. Automation generates your test video
5. Video downloads to `./data/downloads/test_01.mp4`

## 5. Check Results

```bash
# View the downloaded video
ls -lh data/downloads/

# Check logs
tail -f logs/flow_automation.log

# Or open dashboard
streamlit run src/dashboard.py
```

## Next Steps

### Import More Jobs

**From CSV:**
```bash
python scripts/import_prompts.py examples/prompts.csv
```

**From JSON:**
```bash
python scripts/import_prompts.py examples/prompts.json
```

### Generate Prompts with AI

Edit `scripts/generate_script.py`:

```python
#!/usr/bin/env python3
from src.script_writer import ScriptWriter
from src.queue_manager import QueueManager
from src.utils import Config

config = Config()
writer = ScriptWriter(config)
queue = QueueManager()

jobs = writer.generate_prompts(
    topic="A journey through beautiful landscapes",
    num_scenes=5,
    style="cinematic and peaceful"
)

count = queue.add_jobs_bulk(jobs)
print(f"Added {count} jobs to queue")
```

Then run:
```bash
python scripts/generate_script.py
```

### Run Full Automation

```bash
# Process all pending jobs
python scripts/run_automation.py
```

### Monitor Progress

```bash
# Dashboard (real-time monitoring)
streamlit run src/dashboard.py

# Or check logs
tail -f logs/flow_automation.log
```

## Troubleshooting Quick Fixes

### "Element not found"
→ Flow's UI changed. Update `selectors.yaml`

### "Not logged in"
→ Log in manually when browser opens, then press Enter

### "CAPTCHA detected"
→ Your rate limits are too aggressive. Lower them in `.env`

### "FFmpeg not found"
→ Install FFmpeg: `brew install ffmpeg` (macOS)

## Safety Checklist

✅ Started with low rate limits (5/hour, 20/day)  
✅ Updated `selectors.yaml` with current Flow UI  
✅ Using a separate Google account (not your primary)  
✅ Monitoring the first few generations closely  
✅ Ready to create `EMERGENCY_STOP` file if needed  

## Emergency Stop

If something goes wrong:
```bash
touch EMERGENCY_STOP
```

Automation will stop gracefully before the next generation.

---

**Need more details? See the full [README.md](README.md)**
