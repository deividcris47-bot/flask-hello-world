from flask import Flask
import requests, os

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=5)
        return float(r.json()['price'])
    except:
        return 4343.10

@app.route('/')
def home():
    return "V20 ACTIVO - FORMATO COMPRA ✅"

@app.route('/send')
def send():
    p = get_price()
    
    caption = f"""🟢 Compra xauusd 🔥
SL: {p-5.5:.2f}
Entrar en: {p:.2f}
TP1: {p+2.5:.2f}
TP2: {p+5.5:.2f}
TP3: {p+9.5:.2f}

Grafico 👇"""

    # envia solo texto con tu formato + luego el gráfico es opcional
    url_text = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r1 = requests.post(url_text, json={"chat_id": CHAT_ID, "text": caption})

    # Si quieres con foto, usa esta foto que subiste como base
    # Por ahora envia solo texto para probar que llega
    return f"{caption} <br><br> Telegram: {r1.text}"
