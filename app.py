from flask import Flask
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests, os, json
from datetime import datetime
import pytz

app = Flask(__name__)

BOT_TOKEN = "PON_TU_TOKEN"
CHAT_ID = "PON_TU_CHAT_ID"
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
    if hora >= 19 or hora <= 0: return "ASIA"
    elif 2 <= hora <= 6: return "LONDRES"
    else: return "NEW YORK"

@app.route('/send')
def send():
    hoy = str(datetime.now().date())
    data = get_contador()
    if data["fecha"] != hoy:
        data = {"fecha": hoy, "count": 0}
    if data["count"] >= 8:
        return "8 señales completadas"

    # Datos
    m15 = yf.download("GC=F", period="5d", interval="15m", progress=False)
    m5 = yf.download("GC=F", period="2d", interval="5m", progress=False)
    m1 = yf.download("GC=F", period="1d", interval="1m", progress=False)
    
    if len(m1) < 50: return "Sin datos suficientes"

    precio = float(m1['Close'].iloc[-1])
    
    # 1. TENDENCIA 15M
    ema_15 = m15['Close'].ewm(span=20).mean().iloc[-1]
    tendencia_15 = "ALCISTA" if m15['Close'].iloc[-1] > ema_15 else "BAJISTA"
    
    # 2. BOS 15M (Rompimiento)
    bos_alcista_15 = m15['High'].iloc[-1] > m15['High'].tail(20).max()
    bos_bajista_15 = m15['Low'].iloc[-1] < m15['Low'].tail(20).min()
    
    # 3. CHOCH 5M (Cambio de caracter)
    choch_alcista = m5['Close'].iloc[-1] > m5['High'].tail(10).max()
    choch_bajista = m5['Close'].iloc[-1] < m5['Low'].tail(10).min()
    
    # 4. POI - Punto de interes
    swing_high_5 = float(m5['High'].tail(50).max())
    swing_low_5 = float(m5['Low'].tail(50).min())
    zona_premium = swing_low_5 + (swing_high_5 - swing_low_5) * 0.7
    
    # 5. ORDER BLOCK 1M + STRONG
    ob_bull = float(m1['Low'].tail(20).min())
    ob_bear = float(m1['High'].tail(20).max())
    
    # Vela STRONG (cuerpo grande)
    cuerpo_ultimo = abs(m1['Close'].iloc[-1] - m1['Open'].iloc[-1])
    atr = (m1['High'].tail(14).max() - m1['Low'].tail(14).min()) / 14
    es_strong = cuerpo_ultimo > atr * 0.6

    # 6. GATILLO 1M (Engulfing)
    gatillo_buy = m1['Close'].iloc[-1] > m1['Open'].iloc[-1] and m1['Close'].iloc[-1] > m1['High'].iloc[-2]
    
    # 7. NO OPERAR EN ZONA DE RETESTEO
    # Si el precio ya tocó el OB más de 2 veces en las últimas 50 velas, es zona quemada
    toques_ob = ((m1['Low'].tail(50) <= ob_bull + 1) & (m1['Low'].tail(50) >= ob_bull - 1)).sum()
    zona_quemada = toques_ob >= 2

    # CONDICION FINAL SNIPER
    condicion_buy = tendencia_15 == "ALCISTA" and (bos_alcista_15 or choch_alcista) and es_strong and gatillo_buy and not zona_quemada
    condicion_sell = tendencia_15 == "BAJISTA" and (bos_bajista_15 or choch_bajista) and es_strong and not zona_quemada
    
    if not (condicion_buy or condicion_sell):
        return f"Esperando | Tend:{tendencia_15} | BOS:{bos_alcista_15 or bos_bajista_15} | CHOCH:{choch_alcista or choch_bajista} | Strong:{es_strong} | Quemada:{zona_quemada}"

    sesion = get_session()
    data["count"] += 1
    
    if condicion_buy:
        direccion = "Comprar"
        sl = ob_bull - 2.5
        color_ob = 'green'
        zona_ob = ob_bull
    else:
        direccion = "Vender"
        sl = ob_bear + 2.5
        color_ob = 'red'
        zona_ob = ob_bear
        
    tp1 = precio + 5 if direccion == "Comprar" else precio - 5
    tp2 = precio + 10 if direccion == "Comprar" else precio - 10
    tp3 = precio + 20 if direccion == "Comprar" else precio - 20

    # GRAFICO PRO
    plt.figure(figsize=(11,5.5), dpi=150)
    plt.style.use('dark_background')
    plt.plot(m1['Close'].tail(100).values, color='#00ff88', linewidth=1.4, label='Precio 1M')
    plt.axhspan(zona_ob-2, zona_ob+1, color=color_ob, alpha=0.25, label='ORDER BLOCK')
    plt.axhline(swing_high_5, color='gray', linestyle='--', alpha=0.5, label='POI High')
    plt.axhline(swing_low_5, color='gray', linestyle='--', alpha=0.5)
    plt.axhline(precio, color='#00aaff', linestyle='--', linewidth=1.2)
    plt.axhline(sl, color='red', linestyle='-', linewidth=1.2)
    plt.title(f'{sesion} #{data["count"]}/8 | {tendencia_15} | BOS+CHOCH+OB+STRONG', color='white', fontsize=11)
    plt.legend(loc='upper left', fontsize=7)
    plt.grid(alpha=0.15)
    plt.tight_layout()
    plt.savefig('chart.png')
    plt.close()

    if direccion == "Comprar":
        emoji = "🟢"
    else:
        emoji = "🔴"

    mensaje = f"""{emoji} {direccion} XAUUSD 🔥
{sesion} | Tendencia 15M: {tendencia_15}

🛑 SL: {sl:.2f}
🎯 Entrar: {precio:.2f}
✅ TP1: {tp1:.2f}
✅ TP2: {tp2:.2f}
✅ TP3: {tp3:.2f}

BOS:{'✅' if bos_alcista_15 or bos_bajista_15 else '❌'} | CHOCH 5M:{'✅' if choch_alcista or choch_bajista else '❌'} | OB 1M:✅ | POI:✅ | Strong:✅
Zona quemada: {'NO ✅' if not zona_quemada else 'SI ❌'}
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open('chart.png', 'rb') as foto:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': mensaje}, files={'photo': foto})

    save_contador(data)
    return f"Señal {direccion} {data['count']}/8 enviada"

@app.route('/')
def home():
    return "Bot Sniper Pro BOS CHOCH OB POI Activo"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
