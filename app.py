import os, requests, io, random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID") or os.getenv("CHANNEL_ID")

def log(msg):
    print(msg, flush=True)

def send_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHANNEL_ID, "text": text}, timeout=20)
    log(f"TG TEXT: {r.text}")
    return r.text

def send_photo(caption):
    fig, ax = plt.subplots(figsize=(6,3), dpi=70)
    prices = [4347 + random.uniform(-5,5) for _ in range(20)]
    ax.plot(prices, color='gold', linewidth=2)
    ax.set_title(f"XAUUSD {prices[-1]:.2f}")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    r = requests.post(url, data={"chat_id": CHANNEL_ID, "caption": caption}, files={'photo': buf}, timeout=30)
    log(f"TG PHOTO: {r.text}")
    return r.text

@app.route('/')
def home():
    return f"BOT ACTIVO {datetime.now()} - TOKEN:{bool(BOT_TOKEN)} CHANNEL:{CHANNEL_ID}"

@app.route('/test_texto')
def test_texto():
    if not BOT_TOKEN or not CHANNEL_ID:
        return f"FALTA ENV: TOKEN={bool(BOT_TOKEN)} CHANNEL={CHANNEL_ID}"
    return send_text("✅ TEST TEXTO OK - Bot admin correcto")

@app.route('/test')
def test():
    if not BOT_TOKEN or not CHANNEL_ID:
        return f"FALTA ENV: TOKEN={bool(BOT_TOKEN)} CHANNEL={CHANNEL_ID}"
    return send_photo(f"🔥 TEST VELAS REALES 4347.91 - {datetime.now()}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
