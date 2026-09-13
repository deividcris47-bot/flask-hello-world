import os, requests, threading, time
from flask import Flask
from datetime import datetime

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or ""
CHAT_ID = os.environ.get("CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID") or ""

def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        return "Falta BOT_TOKEN o CHAT_ID"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        return r.text
    except Exception as e:
        return str(e)

def get_xau_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json().get("price", 4408))
    except:
        return 4408.0

@app.route("/")
def home():
    return "Bot Deivid V9.1 TELEGRAM - ONLINE 🟢", 200

@app.route("/test")
def test():
    price = get_xau_price()
    msg = f"✅ *TEST V9.1 OK*\n\nBot vivo 🟢\nXAU: *{price}*\nID: `{CHAT_ID}`"
    result = send_telegram(msg)
    return f"Resultado Telegram: {result} | XAU {price}", 200

def bot_loop():
    time.sleep(10)
    send_telegram("🚀 *BOT V9.1 CONECTADO* - Listo para señales XAU")
    while True:
        print(f"XAU: {get_xau_price()}")
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
