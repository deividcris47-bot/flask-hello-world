from flask import Flask
import requests, os

app = Flask(__name__)

@app.route('/')
def home():
    return "V20 TELEGRAM ACTIVO ✅"

@app.route('/send')
def send():
    TOKEN = os.getenv("TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")
    
    # precio real
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=5)
        p = float(r.json()['price'])
    except:
        p = 4343.10

    # TU FORMATO EXACTO QUE PEDISTE
    msg = f"""🟢 Compra xauusd 🔥

SL: {p-5.5:.2f}
Entrar en: {p:.2f}
TP1: {p+4.5:.2f}
TP2: {p+8.5:.2f}
TP3: {p+14.0:.2f}

Grafico 15M 👇"""

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    
    return f"Enviado: {resp.text}<br><br><pre>{msg}</pre>"

@app.route('/senal')
def senal():
    return "Abre /send para probar"
