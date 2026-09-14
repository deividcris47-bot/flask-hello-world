from flask import Flask
import requests, os, io
import matplotlib.pyplot as plt

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=5)
        return float(r.json()['price'])
    except:
        return 4343.10

def make_chart(p):
    plt.figure(figsize=(10,5))
    plt.plot([p-3, p-1, p, p+1], [p-5, p-2, p, p+2], color='green', linewidth=2)
    plt.axhspan(p-0.5, p+0.5, color='green', alpha=0.2)
    plt.title(f"XAUUSD 15M - {p}")
    plt.tight_layout()
    path = "/tmp/xau.png"
    plt.savefig(path)
    plt.close()
    return path

@app.route('/')
def home():
    return "V20 FORMATO COMPRA ACTIVO ✅"

@app.route('/send')
def send():
    p = get_price()
    sl = p - 5.5
    tp1 = p + 4.5
    tp2 = p + 8.5
    tp3 = p + 14.0

    caption = f"""🟢 Compra xauusd 🔥

SL: {sl:.2f}
Entrar en: {p:.2f}
TP1: {tp1:.2f}
TP2: {tp2:.2f}
TP3: {tp3:.2f}

Grafico 15M 👇"""

    chart_path = make_chart(p)
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(chart_path, 'rb') as photo:
        resp = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})
    
    return f"Enviado a Telegram:<br>{resp.text}<br><br><pre>{caption}</pre>"

@app.route('/senal')
def senal():
    return "Abre /send"
