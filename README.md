# iphone_deal_monitor

Production-ready monitor for Orlando that finds new iPad, iPhone, and MacBook listings from Craigslist and Facebook Marketplace, then sends Telegram alerts.

## Features

- Monitors these keywords:
  - `ipad`
  - `iphone`
  - `iphone 15`
  - `iphone 16`
  - `iphone 17`
  - `macbook`
- Sources:
  - Craigslist Orlando RSS
  - Facebook Marketplace Orlando (best-effort public-page parsing)
- Polls every 60 seconds.
- De-duplicates listings using SQLite (never posts same URL twice).
- Configurable filtering via `config.json`:
  - `min_price`
  - `max_price`
  - `required_keywords`
  - `blocked_keywords`
- Telegram alerts with clickable listing links.
- Robust error handling and continuous run loop.
- Simple rate-limiting between requests to avoid hammering source sites.

## Project Structure

- `main.py` - monitor loop and orchestration
- `craigslist.py` - Craigslist RSS collection/parsing
- `marketplace.py` - Facebook Marketplace collection/parsing (best effort)
- `filters.py` - configurable filtering rules
- `db.py` - SQLite seen-listings store
- `notifier.py` - Telegram notification sender
- `config.json` - runtime configuration
- `requirements.txt` - dependencies
- `.env.example` - environment template

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create your environment file:

```bash
cp .env.example .env
```

3. Edit `.env` and fill in:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

4. Tune `config.json` as needed:

- `enable_craigslist`: `true/false`
- `enable_facebook_marketplace`: `true/false`
- filters and delays

## Local Run

```bash
python main.py
```

## Run Continuously (24/7)

### Option A: tmux/screen
Run in a detached terminal session:

```bash
python main.py
```

### Option B: systemd (Linux)
Create `/etc/systemd/system/iphone-deal-monitor.service`:

```ini
[Unit]
Description=iPhone Deal Monitor
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/iphone_deal_monitor
ExecStart=/usr/bin/python3 /path/to/iphone_deal_monitor/main.py
Restart=always
RestartSec=5
EnvironmentFile=/path/to/iphone_deal_monitor/.env

[Install]
WantedBy=multi-user.target
```

Then enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable iphone-deal-monitor
sudo systemctl start iphone-deal-monitor
sudo systemctl status iphone-deal-monitor
```

## Notes

- If Craigslist RSS, Facebook Marketplace parsing, or Telegram API fails temporarily, the app logs errors and keeps running.
- Facebook Marketplace may occasionally require login/challenge pages and yield 0 results for a cycle; this is handled gracefully.
- Filtered and duplicate items are marked as seen to avoid repeated processing.
