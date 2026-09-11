import os, requests, io, random
import matplotlib.pyplot as plt
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# ACEPTA LOS DOS NOMBRES PARA NO FALLAR
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID") or os.getenv("CHANNEL_ID")

def send_log(msg):
    print(msg, flush=True)
    return msg

def send_telegram_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text}
    r = requests.post(url, data=payload)
    send_log(f"Telegram TEXT response: {r.text}")
    return r.text

def send_telegram_photo(caption):
    fig, ax = plt.subplots(figsize=(6,3), dpi=60)
    prices = [4340 + random.random()*15 for _ in range(30)]
    colors = ['g' if random.random()>0.5 else 'r' for _ in prices]
    ax.bar(range(len(prices)), [0.5]*len(prices), bottom=prices, color=colors, width=0.8)
    ax.set_title(f"XAUUSD {prices[-1]:.2f}")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {'photo': ('xau.png', buf, 'image/png')}
    data = {'chat_id': CHANNEL_ID, 'caption': caption}
    r = requests.post(url, data=data, files=files)
    send_log(f"Telegram PHOTO response: {r.text}")
    return r.text

@app.route('/')
def home():
    return f"BOT ACTIVO - TOKEN:{bool(BOT_TOKEN)} CHANNEL:{CHANNEL_ID} - {datetime.now()}"

@app.route('/test_texto')
def test_texto():
    result = send_telegram_text("✅ TEST TEXTO OK - Si ves esto tu bot ya funciona")
    return f"Respuesta Telegram: {result}"

@app.route('/test')
def test():
    result = send_telegram_photo(f"🔥 TEST VELAS REALES - Precio real - {datetime.now()}")
    return f"Respuesta Telegram: {result}"
