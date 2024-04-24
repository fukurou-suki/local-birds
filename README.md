# Local Birds Alert
Send email alert or Telegram alert on local birds reports.
Data source: eBird

## Requirements
Python >= 3

## Quick Start

### Install Dependencies
After cloning the repo, under the root directory, run
```
pip install -r requirements.txt
```

### Create .env File
The app uses `.env` to manage configs and secrets, to create `.env` file run
```
cp local-birds/.env.template local-birds/.env
```

### Get eBird API Key
Get an eBird account if you haven't, then get the API key via https://ebird.org/api/keygen. Paste the key to `EBIRD_API_KEY` in your `.env` file.

### Email Alert Setup
To enable the email alert, set `ENABLE_EMAIL_ALERT=true` in your `.env` file.

Configure the rest of email related settings in `.env` to proceed.

If you are using Gmail as sender, generate the app password [here](https://myaccount.google.com/apppasswords).

### Telegram Alert Setup
To enable the Telegram alert, set `ENABLE_TELEGRAM_ALERT=true` in your `.env` file.

#### Create Telegram Bot
Open your Telegram app, search for `BotFather` and send this command to create a Telegram bot
```
/newbot
```
Follow the prompts until you get the bot token. Paste your bot token to `TELEGRAM_BOT_TOKEN` in your `.env` file.

#### Create Group Chat
Create a Telegram group and add the bot there. Send a test message to the bot in order to get the chat id
```
/test @{bot_id}
```
Open your browser and enter this URL `https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates` to get the chat id, copy the value under `message > chat > id` and paste it to `TELEGRAM_CHAT_ID` in your `.env` file.

You are all set!

### Run
Under the root directory, run
```
python local-birds/__init__.py

```
Check your email and/or Telegram!
