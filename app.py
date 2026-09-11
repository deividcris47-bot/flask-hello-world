import os, requests
from flask import Flask

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHANNEL_ID") or os.getenv("CHANNEL_ID")

@app.route('/')
def home():
    return f"OK TOKEN:{bool(TOKEN)} CHAT:{CHAT} - BOT VIVO"

@app.route('/test_texto')
def test():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT, "text": "✅ TEST FINAL - SI VES ESTO EN TELEGRAM YA FUNCIONO"})
    return r.text
