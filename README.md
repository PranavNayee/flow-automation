# Flow Automation Tool

**Browser automation for batch video generation using Google Flow (Veo)**

⚠️ **IMPORTANT DISCLAIMER**

This tool automates interaction with Google Flow, which may violate Google's Terms of Service. Using this tool could result in:
- Account suspension or termination
- Loss of access to Google services
- Violation of rate limits and abuse detection systems

**Use at your own risk. This is for educational purposes only.**

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [First-Time Setup](#first-time-setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Flow UI Changes](#flow-ui-changes)
- [Architecture](#architecture)
- [Safety Features](#safety-features)
- [Troubleshooting](#troubleshooting)
- [YouTube Upload](#youtube-upload)

---

## Features

✅ **Persistent Browser Profile** - Log in once, stay logged in  
✅ **Intelligent Queue Management** - SQLite-based job queue with resume capability  
✅ **Human-like Behavior** - Random delays, configurable rate limits  
✅ **Safety First** - Automatic CAPTCHA detection, stops on warnings  
✅ **Health Checks** - Validates UI selectors before each run  
✅ **Credit Tracking** - Monitor usage against your plan limits  
✅ **Video Editing** - Stitch clips, add audio/subtitles with FFmpeg  
✅ **LLM Script Generation** - Generate scene prompts from topics  
✅ **Streamlit Dashboard** - Monitor progress, preview videos, approve/reject  
✅ **YouTube Upload** - Automated upload with required AI disclosure flags  

---

## Requirements

### System Requirements
- **Python 3.11+**
- **macOS, Linux, or Windows**
- **4GB RAM minimum** (8GB+ recommended)
- **Stable internet connection**

### Software Dependencies
- **FFmpeg** (for video editing)
- **Playwright** (browser automation)
- **Optional:** OpenAI or Anthropic API key (for script generation)
- **Optional:** Google Cloud credentials (for YouTube upload)

---

## Installation

### 1. Clone or Download

```bash
cd /path/to/your/projects
# (This README assumes you already have the code)
```

### 2. Create Virtual Environment

```bash
cd flow-automation
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Playwright Browser

```bash
playwright install chromium
```

### 5. Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH

**Verify installation:**
```bash
ffmpeg -version
```

---

## First-Time Setup

### 1. Initialize the Project

```bash
python scripts/init_db.py
```

This creates:
- Database and directories
- `.gitkeep` files
- Emergency stop template

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Rate limits (CRITICAL - start conservative!)
MAX_GENERATIONS_PER_HOUR=5
MAX_GENERATIONS_PER_DAY=20

# Browser profile
BROWSER_PROFILE_PATH=./playwright-state

# Optional: LLM API for script generation
OPENAI_API_KEY=sk-...

# Optional: Monthly credit limit (your Flow plan)
MONTHLY_CREDIT_LIMIT=100
```

### 3. Update Selectors (IMPORTANT!)

**Before running, you MUST verify Flow's current UI selectors:**

1. Open Flow in your browser: https://labs.google/flow
2. Open DevTools (F12 or Cmd+Opt+I)
3. Use Element Picker (Ctrl+Shift+C / Cmd+Shift+C)
4. Click on each UI element:
   - Prompt textarea
   - Generate button
   - Video preview area
   - Download button

5. For each element:
   - Right-click in Elements tab → Copy → Copy selector
   - Update `selectors.yaml` with the correct selector
   - **Prefer:** `data-testid`, `aria-label`, or semantic HTML
   - **Avoid:** CSS classes (they change frequently)

6. Update the "Last verified" date in `selectors.yaml`

### 4. First Login

The first time you run the automation, you'll need to log in manually:

```bash
python scripts/run_automation.py
```

The browser will open. If you're not logged in:
1. Log in to your Google account
2. Navigate to Flow
3. Complete any 2FA challenges
4. Press Enter in the terminal to continue

Your login session is saved in `./playwright-state/` and persists across runs.

---

## Configuration

### Rate Limits (`MAX_GENERATIONS_PER_HOUR`, `MAX_GENERATIONS_PER_DAY`)

**Start conservative!** Google's systems detect unusual activity:

- **Recommended starting point:** 5/hour, 20/day
- **Aggressive:** 10/hour, 50/day (higher risk)
- Monitor for warnings and adjust accordingly

### Delays (`MIN_DELAY_BETWEEN_GENERATIONS`, `MAX_DELAY_BETWEEN_GENERATIONS`)

Random delays between generations to mimic human behavior:

- **Conservative:** 120-300 seconds (2-5 minutes)
- **Default:** 60-180 seconds (1-3 minutes)
- **Aggressive:** 30-90 seconds (higher risk)

### Selectors (`selectors.yaml`)

All UI selectors in one place. When Flow's UI changes, update this file.

**Selector Priority:**
1. `[data-testid="..."]` ⭐ Most stable
2. `[aria-label="..."]` ⭐ Accessible, stable
3. `#id` - Good if present
4. `button[type="submit"]` - Semantic
5. `.css-class` ⚠️ Least stable

---

## Usage

### Import Prompts

**From CSV:**
```bash
python scripts/import_prompts.py examples/prompts.csv
```

**From JSON:**
```bash
python scripts/import_prompts.py examples/prompts.json
```

**CSV Format:**
```csv
scene_id,prompt,aspect_ratio,duration
scene_01,"A mountain at sunrise...",16:9,5
```

**JSON Format:**
```json
[
  {
    "scene_id": "scene_01",
    "prompt": "A mountain at sunrise...",
    "aspect_ratio": "16:9",
    "duration": 5
  }
]
```

### Generate Scene Prompts with LLM

```python
from src.script_writer import ScriptWriter
from src.utils import Config
from src.queue_manager import QueueManager

config = Config()
writer = ScriptWriter(config)
queue = QueueManager()

# Generate prompts for a topic
jobs = writer.generate_prompts(
    topic="A journey through the four seasons",
    num_scenes=8,
    aspect_ratio="16:9",
    style="cinematic"
)

# Add to queue
queue.add_jobs_bulk(jobs)
```

### Run the Automation

```bash
python scripts/run_automation.py
```

**What happens:**
1. Health check validates UI selectors
2. Browser opens (or reuses session)
3. For each job in queue:
   - Navigate to Flow
   - Check for warnings/CAPTCHA
   - Enter prompt
   - Set options (aspect ratio, etc.)
   - Click generate
   - Wait for completion
   - Download video
   - Apply rate limits and delays
4. Saves all videos to `./data/downloads/`

**Resume capability:** If the script crashes or you stop it (Ctrl+C), running it again will resume from where it left off. Jobs marked as "running" are automatically reset to "pending".

### Monitor with Dashboard

```bash
streamlit run src/dashboard.py
```

Opens at http://localhost:8501

Features:
- Real-time queue status
- Credit usage tracking
- Rate limit monitoring
- Preview completed videos
- Approve/reject for upload

### Emergency Stop

Create this file to stop immediately:

```bash
touch EMERGENCY_STOP
```

The automation checks for this file before each generation and stops gracefully.

---

## Flow UI Changes

**Flow's UI changes frequently.** When selectors break:

### 1. Run Health Check

The automation runs health checks automatically, but you can test manually:

```python
from playwright.sync_api import sync_playwright
from src.health_check import HealthChecker, generate_selector_update_guide
from src.utils import SelectorsConfig

selectors = SelectorsConfig()
checker = HealthChecker(selectors)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://labs.google/flow")
    
    result = checker.run_full_check(page)
    
    if not result.passed:
        guide = generate_selector_update_guide(result)
        print(guide)
```

### 2. Update Selectors

When a selector breaks, the tool generates `SELECTOR_UPDATE_GUIDE.md` with instructions.

**Steps:**
1. Open Flow in browser
2. Open DevTools (F12)
3. Enable Element Picker (Ctrl+Shift+C)
4. Click the UI element
5. Right-click in Elements panel → Copy → Copy selector
6. Update `selectors.yaml`
7. Test: `python scripts/run_automation.py`

### 3. Test Before Full Run

After updating selectors, test with a single job:

```bash
# Import just one test job
echo 'scene_id,prompt,aspect_ratio,duration
test_01,"A simple test scene",16:9,5' > test.csv

python scripts/import_prompts.py test.csv --clear
python scripts/run_automation.py
```

---

## Architecture

### Module Overview

```
flow-automation/
├── src/
│   ├── queue_manager.py      # SQLite job queue
│   ├── flow_driver.py         # Playwright automation
│   ├── downloader.py          # Video download
│   ├── health_check.py        # Selector validation
│   ├── credit_tracker.py      # Usage monitoring
│   ├── editor.py              # FFmpeg video editing
│   ├── script_writer.py       # LLM prompt generation
│   ├── dashboard.py           # Streamlit UI
│   ├── uploader.py            # YouTube API
│   └── utils/                 # Config, logging, delays
├── scripts/
│   ├── init_db.py            # Initialize project
│   ├── import_prompts.py     # Load jobs from CSV/JSON
│   └── run_automation.py     # Main automation loop
├── config.yaml               # Application config
├── selectors.yaml            # UI selectors (update when Flow changes)
└── .env                      # Secrets and limits
```

### Data Flow

```
1. CSV/JSON → queue_manager → SQLite queue
2. run_automation.py → flow_driver → Browser automation
3. flow_driver → Flow UI → Generated video
4. downloader → Save video file
5. editor → Stitch/enhance videos
6. uploader → YouTube with AI disclosure
```

### Job States

- **pending** - Waiting to be processed
- **running** - Currently generating
- **completed** - Successfully generated and downloaded
- **failed** - Failed after max retries
- **retry** - Failed but will retry

---

## Safety Features

### 1. Rate Limiting
- Hourly and daily generation limits
- Enforced before each generation
- Configurable in `.env`

### 2. Credit Tracking
- Monitors monthly usage
- Stops when limit reached
- Persists across sessions

### 3. Warning Detection
- Automatic CAPTCHA detection
- Rate limit warning detection
- Stops immediately on detection
- Screenshots saved for debugging

### 4. Human-like Behavior
- Random delays between actions
- Random typing speed
- Variable generation intervals
- Non-automation browser fingerprint

### 5. Emergency Stop
- Create `EMERGENCY_STOP` file
- Checked before each generation
- Graceful shutdown

### 6. Resume Safety
- Crashed jobs reset to pending
- No duplicate generations (scene_id is unique)
- Transaction-safe database updates

---

## Troubleshooting

### "Element not found" or timeout errors

**Cause:** Flow's UI has changed.

**Fix:**
1. Check `SELECTOR_UPDATE_GUIDE.md` (auto-generated)
2. Update `selectors.yaml`
3. Test with single job

### "Not logged in" or CAPTCHA appears

**Cause:** Session expired or suspicious activity detected.

**Fix:**
1. Log in manually in the browser window
2. Complete CAPTCHA if present
3. Reduce rate limits in `.env`
4. Increase delays between generations

### Download fails but generation succeeds

**Cause:** Download method has changed.

**Fix:**
1. Update `main.download_button` selector in `selectors.yaml`
2. Check if Flow changed from button to right-click menu
3. Inspect browser console for errors

### "FFmpeg not found"

**Cause:** FFmpeg not installed or not in PATH.

**Fix:**
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg

# Verify
ffmpeg -version
```

### Rate limit warnings appearing

**Cause:** Generating too fast.

**Fix:**
1. Increase `MIN_DELAY_BETWEEN_GENERATIONS` (e.g., 120)
2. Decrease `MAX_GENERATIONS_PER_HOUR` (e.g., 3)
3. Wait 24 hours before resuming

### Database locked errors

**Cause:** Multiple processes accessing database.

**Fix:**
- Only run one instance of `run_automation.py`
- Close Streamlit dashboard before running automation

---

## YouTube Upload

### Setup OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable **YouTube Data API v3**
4. Create OAuth 2.0 credentials:
   - Application type: Desktop app
   - Download JSON as `client_secret.json`
5. Place in project root:
   ```
   flow-automation/
   ├── client_secret.json  ← here
   ```

### First Upload (Authorization)

```python
from src.uploader import YouTubeUploader
from src.utils import Config

config = Config()
uploader = YouTubeUploader(config)

# Browser will open for OAuth flow
# Approve access → credentials saved to token.pickle

video_id = uploader.upload_video(
    video_path="./data/projects/my_video.mp4",
    title="AI-Generated Video Test",
    description="This video was created using AI (Google Veo)",
    tags=["AI", "Veo", "Test"],
    privacy_status="private"  # Start with private!
)

print(f"Uploaded: https://www.youtube.com/watch?v={video_id}")
```

### AI Content Disclosure

**IMPORTANT:** YouTube requires disclosure for AI-generated content.

This tool automatically sets:
```python
'contentDetails': {
    'hasAlteredOrSyntheticContent': True
}
```

You MUST also:
1. Check "Altered content" in YouTube Studio after upload
2. Add disclosure in description: "This video was generated using AI"

**Failure to disclose AI content violates YouTube's policies.**

### Upload Limits

YouTube API quota: **10,000 units/day**
- Each upload: ~1,600 units
- **≈6 uploads per day**

---

## Advanced Usage

### Stitch Multiple Scenes

```python
from src.editor import VideoEditor
from src.utils import Config

config = Config()
editor = VideoEditor(config)

videos = [
    "./data/downloads/scene_01.mp4",
    "./data/downloads/scene_02.mp4",
    "./data/downloads/scene_03.mp4"
]

output = editor.stitch_videos(
    video_paths=videos,
    output_name="final_video",
    transition_duration=0.5
)

print(f"Stitched video: {output}")
```

### Add Background Music

```python
output = editor.add_audio(
    video_path="./data/projects/final_video.mp4",
    audio_path="./music/background.mp3",
    output_name="final_with_music",
    audio_volume=0.3  # 30% volume
)
```

### Add Subtitles

```python
# Create SRT file first
srt_content = """1
00:00:00,000 --> 00:00:05,000
Welcome to our video

2
00:00:05,000 --> 00:00:10,000
Enjoy the journey
"""

with open("subtitles.srt", "w") as f:
    f.write(srt_content)

output = editor.add_subtitles(
    video_path="./data/projects/final_with_music.mp4",
    srt_path="subtitles.srt",
    output_name="final_complete",
    font="Arial",
    font_size=24
)
```

---

## Best Practices

### For Long-Running Sessions

1. **Start small:** Test with 2-3 jobs first
2. **Monitor closely:** Watch the first few generations
3. **Increase gradually:** If no warnings, increase rate limits slowly
4. **Use dashboard:** Keep Streamlit dashboard open to monitor
5. **Check logs:** Review `./logs/flow_automation.log` regularly

### For Production Use

1. **Separate account:** Use a dedicated Google account, not your primary
2. **VPN consideration:** Consider using a VPN to avoid IP-based detection
3. **Time of day:** Generate during off-peak hours (less load = less detection)
4. **Batch size:** Process 10-20 videos, then pause for several hours
5. **Backup prompts:** Keep CSV/JSON files backed up

### Staying Under the Radar

1. **Conservative limits:** 5/hour, 20/day maximum
2. **Long delays:** 2-5 minutes between generations
3. **Weekend breaks:** Don't run 24/7, take breaks
4. **Manual activity:** Occasionally use Flow manually to appear human
5. **Error handling:** Stop immediately on any warning

---

## Contributing

This is a personal automation tool. Use at your own risk.

If Flow's UI changes significantly, update `selectors.yaml` and document the changes.

---

## License

MIT License - See LICENSE file

---

## Disclaimer (Again!)

⚠️ **THIS TOOL MAY VIOLATE GOOGLE'S TERMS OF SERVICE**

- Automation of web services is generally prohibited
- Account suspension is a real risk
- Use only with accounts you can afford to lose
- The authors are not responsible for any consequences
- This is provided for educational purposes only

**By using this tool, you acknowledge these risks and accept full responsibility.**

---

## Support

For issues with:
- **Flow UI changes:** Update `selectors.yaml` (see "Flow UI Changes" section)
- **Configuration:** Check `.env` and `config.yaml`
- **Playwright:** https://playwright.dev/python/docs/intro
- **FFmpeg:** https://ffmpeg.org/documentation.html

---

**Happy (careful) automating! 🎬**
