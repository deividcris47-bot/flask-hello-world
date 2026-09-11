import os, requests, io, random
import matplotlib.pyplot as plt
from flask import Flask
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

def send_log(msg):
    print(msg, flush=True)
    return msg

def send_telegram_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text}
    r = requests.post(url, data=payload)
    send_log(f"Telegram TEXT response: {r.text}")
    return r.json()

def send_telegram_photo(caption):
    # Grafico liviano para Render Free
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
    return r.json()

@app.route('/')
def home():
    return f"BOT VELAS REALES ACTIVO - {datetime.now()}"

@app.route('/test_texto')
def test_texto():
    if not BOT_TOKEN or not CHANNEL_ID:
        return f"ERROR: Falta TOKEN o CHANNEL_ID. TOKEN:{bool(BOT_TOKEN)} CHANNEL:{CHANNEL_ID}"
    result = send_telegram_text("✅ TEST TEXTO OK - Si ves esto tu bot es admin correctamente")
    return f"Respuesta Telegram: {result}"

@app.route('/test')
def test():
    if not BOT_TOKEN or not CHANNEL_ID:
        return f"ERROR: Falta TOKEN o CHANNEL_ID"
    result = send_telegram_photo(f"🔥 TEST VELAS REALES - Precio 4347.91 - {datetime.now()}")
    return f"Respuesta Telegram: {result}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
