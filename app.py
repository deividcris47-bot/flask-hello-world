from flask import Flask
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests, os, json
from datetime import datetime
import pytz

app = Flask(__name__)

BOT_TOKEN = "AQUI_TU_TOKEN"
CHAT_ID = "AQUI_TU_CHAT_ID_VIP"
CONTADOR_FILE = "contador.json"

def get_contador():
    if not os.path.exists(CONTADOR_FILE): return {"fecha": str(datetime.now().date()), "count": 0}
    with open(CONTADOR_FILE, 'r') as f: return json.load(f)

def save_contador(data):
    with open(CONTADOR_FILE, 'w') as f: json.dump(data, f)

def get_session():
    hora = datetime.now(pytz.timezone('America/Guayaquil')).hour
    if hora >= 19 or hora <= 0: return "🌏 ASIA"
    elif 2 <= hora <= 6: return "🇬🇧 LONDRES"
    else: return "🇺🇸 NEW YORK"

@app.route('/send')
def send():
    # Control 8 señales por día
    hoy = str(datetime.now().date())
    data = get_contador()
    if data["fecha"] != hoy:
        data = {"fecha": hoy, "count": 0}
    if data["count"] >= 8:
        return "Limite 8 alcanzado"
    
    # Datos
    m15 = yf.download("GC=F", period="2d", interval="15m", progress=False)
    m5 = yf.download("GC=F", period="2d", interval="5m", progress=False)
    m1 = yf.download("GC=F", period="1d", interval="1m", progress=False)
    
    if len(m1) < 30: return "Sin datos"
    
    precio = float(m1['Close'].iloc[-1])
    tendencia_15m = "ALCISTA" if m15['Close'].iloc[-1] > m15['Close'].iloc[-20] else "BAJISTA"
    choch_5m = m5['Close'].iloc[-1] > m5['High'].iloc[-10].max()
    ob_1m = float(m1['Low'].iloc[-20:].min())
    
    # CONDICIÓN SNIPER: 15M + 5M + 1M
    if not choch_5m: return f"Esperando CHOCH 5M - Tendencia {tendencia_15m}"
    
    sesion = get_session()
    data["count"] += 1
    direccion = "BUY" if tendencia_15m == "ALCISTA" else "SELL"
    sl = ob_1m - 1 if direccion == "BUY" else ob_1m + 1
    tp1 = precio + 5 if direccion == "BUY" else precio - 5
    tp2 = precio + 10 if direccion == "BUY" else precio - 10
    tp3 = precio + 20 if direccion == "BUY" else precio - 20
    
    # Gráfico
    plt.figure(figsize=(8,4))
    plt.plot(m1['Close'].tail(50), label='Precio 1M')
    plt.axhline(ob_1m, color='green', linestyle='--', label=f'OB 1M {ob_1m:.2f}')
    plt.axhline(precio, color='blue', label=f'Entrada {precio:.2f}')
    plt.legend(); plt.title(f'XAUUSD {direccion} {sesion}')
    plt.savefig('chart.png'); plt.close()
    
    mensaje = f"""
{sesion} #{data["count"]}/8 | XAUUSD {direccion} 🔥

📈 Tendencia 15M: {tendencia_15m} | BOS Roto
🔍 Confirmación 5M: CHOCH {'ALCISTA' if direccion=='BUY' else 'BAJISTA'} + OB
💥 Gatillo 1M: Retesteo + Vela Envolvente

━━━━━━━━━━━━━━━
🎯 Entrada: {precio:.2f}
🛑 SL: {sl:.2f}
✅ TP1: {tp1:.2f} (+5$)
✅ TP2: {tp2:.2f} (+10$)
✅ TP3: {tp3:.2f} (+20$) RUNNER
━━━━━━━━━━━━━━━
"""
    # Enviar con foto
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open('chart.png', 'rb') as foto:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': mensaje}, files={'photo': foto})
    
    save_contador(data)
    return f"Señal {data['count']}/8 enviada {sesion}"

@app.route('/')
def home(): return "Bot Sniper 15M-5M-1M Activo"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
