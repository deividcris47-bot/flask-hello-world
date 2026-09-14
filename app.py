from flask import Flask
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests, os, json
from datetime import datetime
import pytz

app = Flask(__name__)

BOT_TOKEN = "PON_AQUI_TU_BOT_TOKEN"
CHAT_ID = "PON_AQUI_TU_CHAT_ID"
CONTADOR_FILE = "contador.json"

def get_contador():
    if not os.path.exists(CONTADOR_FILE):
        return {"fecha": str(datetime.now().date()), "count": 0}
    with open(CONTADOR_FILE, 'r') as f:
        return json.load(f)

def save_contador(data):
    with open(CONTADOR_FILE, 'w') as f:
        json.dump(data, f)

def get_session():
    hora = datetime.now(pytz.timezone('America/Guayaquil')).hour
    if hora >= 19 or hora <= 0:
        return "ASIA"
    elif 2 <= hora <= 6:
        return "LONDRES"
    else:
        return "NEW YORK"

@app.route('/send')
def send():
    hoy = str(datetime.now().date())
    data = get_contador()
    if data["fecha"] != hoy:
        data = {"fecha": hoy, "count": 0}
    if data["count"] >= 8:
        return "8 senales completadas hoy"

    m15 = yf.download("GC=F", period="2d", interval="15m", progress=False)
    m5 = yf.download("GC=F", period="2d", interval="5m", progress=False)
    m1 = yf.download("GC=F", period="1d", interval="1m", progress=False)

    if len(m1) < 30:
        return "Sin datos"

    precio = float(m1['Close'].iloc[-1])
    tendencia = "ALCISTA" if m15['Close'].iloc[-1] > m15['Close'].iloc[-20] else "BAJISTA"
    ob_1m = float(m1['Low'].tail(20).min())
    choch = m5['Close'].iloc[-1] > m5['High'].tail(10).max()

    if not choch:
        return f"Esperando CHOCH - Tendencia {tendencia}"

    sesion = get_session()
    data["count"] += 1
    sl = ob_1m - 1
    tp1 = precio + 5
    tp2 = precio + 10
    tp3 = precio + 20

    # GRAFICO
    plt.figure(figsize=(10,5), dpi=150)
    plt.style.use('dark_background')
    plt.plot(m1['Close'].tail(80).values, color='#00ff88', linewidth=1.5)
    plt.axhspan(ob_1m-2, ob_1m, color='green', alpha=0.25)
    plt.axhline(precio, color='#00aaff', linestyle='--')
    plt.axhline(sl, color='red', linestyle='--')
    plt.axhline(tp1, color='gold', linestyle=':')
    plt.axhline(tp2, color='gold', linestyle=':')
    plt.axhline(tp3, color='gold', linestyle=':', linewidth=1.5)
    plt.title(f'{sesion} #{data["count"]}/8 | XAUUSD BUY | 15M-5M-1M', color='white', fontsize=11)
    plt.grid(alpha=0.15)
    plt.tight_layout()
    plt.savefig('chart.png')
    plt.close()

    # FORMATO QUE PEDISTE
    mensaje = f"""🟢 Comprar XAUUSD 🔥

🛑 SL: {sl:.2f}
🎯 Entrar: {precio:.2f}
✅ TP1: {tp1:.2f}
✅ TP2: {tp2:.2f}
✅ TP3: {tp3:.2f}
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open('chart.png', 'rb') as foto:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': mensaje}, files={'photo': foto})

    save_contador(data)
    return f"Senal {data['count']}/8 {sesion} enviada"

@app.route('/')
def home():
    return "Bot Sniper 8 Senales Activo"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
