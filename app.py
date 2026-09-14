from flask import Flask
import requests, os
app = Flask(__name__)

@app.route('/test_token')
def test_token():
    TOKEN = (os.getenv("BOT_TOKEN") or os.getenv("TOKEN") or "").strip()
    r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe").json()
    return str(r)

@app.route('/send')
def send():
    TOKEN = (os.getenv("BOT_TOKEN") or os.getenv("TOKEN") or "").strip()
    CHAT_ID = (os.getenv("CHAT_ID") or "").strip()
    p = 4343.10
    try:
        p = float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=5).json()['price'])
    except: pass
    msg = f"🟢 Compra xauusd 🔥\n\nSL: {p-5.5:.2f}\nEntrar en: {p:.2f}\nTP1: {p+4.5:.2f}\nTP2: {p+8.5:.2f}\nTP3: {p+14.0:.2f}\n\nGrafico 15M 👇"
    resp = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg}).json()
    return f"{resp}<br><pre>{msg}</pre>"

@app.route('/')
def home():
    return "V20 OK"
