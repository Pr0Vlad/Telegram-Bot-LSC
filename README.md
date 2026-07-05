# Telegram Bot LSC

Telegram bot for the LSC video team. It reads service plans from Planning Center, responds with team schedules, sends birthday messages, and can start Planning Center autoscheduling for the nearest future Sunday service plans.

## Features

- Reply with upcoming Sunday, Communion, Wednesday, or next service schedules.
- Start autoscheduling for the nearest future Sunday service plans.
- Run autoscheduling against a configured test plan.
- Send today's video team birthdays.
- Send a daily birthday message to the configured real group chat.

## Requirements

- Python 3.10 or newer
- A Telegram bot token
- Planning Center API credentials

## Python Libraries

Install this third-party library:

- `python-telegram-bot[job-queue]`

The rest of the imports are included with Python 3.10:

- `base64`
- `datetime`
- `json`
- `os`
- `re`
- `typing`
- `urllib`
- `zoneinfo`

Install dependencies:

```powershell
py -3.10 -m pip install "python-telegram-bot[job-queue]"
```

## Configuration

Set these environment variables before running the bot:

```powershell
$env:TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
$env:TELEGRAM_BOT_USERNAME = "@your_bot_username"
$env:PLANNING_CENTER_APP_ID = "your-planning-center-app-id"
$env:PLANNING_CENTER_SECRET = "your-planning-center-secret"
```

The group chat IDs, birthday time, Planning Center service type, and video team IDs are currently configured in the Python files.

## Run

```powershell
py -3.10 LSCService.py
```

The bot starts polling Telegram and schedules the daily birthday check for 9:00 AM America/New_York.

## Bot Commands

- `/start` - welcome message
- `/help` - help message
- `/custom` - custom message
- `/birthdays` - check today's video team birthdays
- `/autoschedule` - start autoscheduling for the nearest future Sunday service plans
- `/testautoschedule` - start autoscheduling for the configured test plan

The bot also responds to text messages such as:

- `auto schedule`
- `test auto schedule`
- `sunday schedule 1`
- `sunday schedule 2`
- `sunday schedule *`
- `communion schedule 1`
- `wednesday schedule`
- `next schedule`

In group chats, include the bot username in the message so the bot knows to respond.

## Autoscheduling

`/autoschedule` calls Planning Center for future plans, filters them to Sunday plans, picks the nearest Sunday date, and starts autoscheduling for every service plan on that date.

For example, if today is Sunday and Planning Center still returns today's services as future plans, the bot will schedule today's Sunday services. Once those services are no longer returned as future plans, it will move to the next future Sunday.

## Security

Do not commit live Telegram or Planning Center credentials. This repo reads credentials from environment variables so secrets can stay outside source control.
