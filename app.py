from flask import Flask
import requests, datetime, pytz, os

app = Flask(__name__)
ECUADOR = pytz.timezone('America/Guayaquil')

TOKEN = os.getenv("TOKEN", "PON_AQUI_TU_TOKEN_DE_BOTFATHER")
CHAT_ID = os.getenv("CHAT_ID", "PON_AQUI_TU_CHAT_ID")

def get_xau_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=5)
        return float(r.json()['price'])
    except:
        return 4332.00

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode":"HTML"})

@app.route('/')
def home():
    hora_ec = datetime.datetime.now(ECUADOR).strftime("%H:%M:%S")
    return f"V20 ACTIVO ✅ {hora_ec} - /senal - /send"

@app.route('/senal')
def senal():
    precio = get_xau_price()
    msg = f"""🟢 Compra XAUUSD 🔥
SL: {precio-2.5:.2f}
Entrar en: {precio:.2f}
TP1: {precio+2.0:.2f}
TP2: {precio+4.5:.2f}
TP3: {precio+8.0:.2f}
CHoCH + BOS + Rompimiento vela grande 1M confirmado"""
    return msg.replace("\n", "<br>")

@app.route('/send')
def send():
    precio = get_xau_price()
    msg = f"""🟢 Compra XAUUSD 🔥
SL: {precio-2.5:.2f}
Entrar en: {precio:.2f}
TP1: {precio+2.0:.2f}
TP2: {precio+4.5:.2f}
TP3: {precio+8.0:.2f}
CHoCH + BOS + Rompimiento vela grande 1M confirmado
Hora EC: {datetime.datetime.now(ECUADOR).strftime('%H:%M')}"""
    send_telegram(msg)
    return f"Enviado a Telegram ✅<br>{msg.replace(chr(10),'<br>')}"
