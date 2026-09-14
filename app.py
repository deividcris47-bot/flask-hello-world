from flask import Flask
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests, os, json
from datetime import datetime
import pytz
from flask import request

app = Flask(__name__)

# --- PON TUS DATOS AQUI ---
BOT_TOKEN = "TU_TOKEN_AQUI_7123:AAH..."
CHAT_ID = "TU_CHAT_ID_AQUI_12345"
# --------------------------

CONTADOR_FILE = "contador.json"

def get_contador():
    if not os.path.exists(CONTADOR_FILE):
        return {"fecha": str(datetime.now().date()), "count": 0}
    try:
        with open(CONTADOR_FILE, 'r') as f: return json.load(f)
    except: return {"fecha": str(datetime.now().date()), "count": 0}

def save_contador(data):
    with open(CONTADOR_FILE, 'w') as f: json.dump(data, f)

def get_session():
    hora = datetime.now(pytz.timezone('America/Guayaquil')).hour
    if hora >= 19 or hora <= 1: return "🌙 ASIA"
    elif 2 <= hora <= 6: return "🇬🇧 LONDRES"
    else: return "🇺🇸 NEW YORK"

def enviar_telegram(foto_path, mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(foto_path, 'rb') as foto:
        r = requests.post(url, data={'chat_id': CHAT_ID, 'caption': mensaje, 'parse_mode': 'Markdown'}, files={'photo': foto}, timeout=20)
    return r.text

@app.route('/send')
def send():
    es_prueba = request.args.get('test') == '1'
    
    hoy = str(datetime.now().date())
    data = get_contador()
    if data["fecha"] != hoy: data = {"fecha": hoy, "count": 0}
    if data["count"] >= 8 and not es_prueba:
        return f"8 señales completadas hoy - {hoy}"

    ticker = "XAUUSD=X"
    m15 = yf.download(ticker, period="7d", interval="15m", progress=False, auto_adjust=True)
    m5 = yf.download(ticker, period="7d", interval="5m", progress=False, auto_adjust=True)
    m1 = yf.download(ticker, period="7d", interval="1m", progress=False, auto_adjust=True)
    
    if len(m1) < 30 and not es_prueba:
        return f"Mercado cerrado fin de semana | Velas 1M: {len(m1)} | El domingo 5pm abre"

    precio = float(m1['Close'].iloc[-1]) if len(m1) > 0 else 4330.44
    ema_15 = float(m15['Close'].ewm(span=20).mean().iloc[-1]) if len(m15)>0 else precio
    tendencia_15 = "ALCISTA" if precio > ema_15 else "BAJISTA"
    
    # Lógica sniper
    if es_prueba:
        direccion = "Comprar"; condicion_buy = True; zona_quemada = False
        sl = precio - 3.5; tp1, tp2, tp3 = precio+5, precio+10, precio+20
        tendencia_15 = "ALCISTA"; sesion = get_session() + " | PRUEBA"
        bos_ok = True; choch_ok = True
    else:
        bos_alcista = float(m15['High'].iloc[-1]) >= float(m15['High'].tail(20).max()) if len(m15)>20 else False
        bos_bajista = float(m15['Low'].iloc[-1]) <= float(m15['Low'].tail(20).min()) if len(m15)>20 else False
        choch_alcista = float(m5['Close'].iloc[-1]) > float(m5['High'].tail(10).max()) if len(m5)>10 else False
        choch_bajista = float(m5['Close'].iloc[-1]) < float(m5['Low'].tail(10).min()) if len(m5)>10 else False
        ob_bull = float(m1['Low'].tail(20).min()); ob_bear = float(m1['High'].tail(20).max())
        cuerpo = abs(float(m1['Close'].iloc[-1]) - float(m1['Open'].iloc[-1])); es_strong = cuerpo > 0.8
        gatillo_buy = float(m1['Close'].iloc[-1]) > float(m1['Open'].iloc[-1])
        toques = ((m1['Low'].tail(50) <= ob_bull+2) & (m1['Low'].tail(50) >= ob_bull-2)).sum(); zona_quemada = toques >= 3
        
        condicion_buy = (tendencia_15 == "ALCISTA" and (bos_alcista or choch_alcista) and es_strong and gatillo_buy and not zona_quemada)
        condicion_sell = (tendencia_15 == "BAJISTA" and (bos_bajista or choch_bajista) and es_strong and not gatillo_buy and not zona_quemada)
        
        if not (condicion_buy or condicion_sell):
            return f"Esperando sniper | Tend:{tendencia_15} | BOS:{bos_alcista or bos_bajista} | CHOCH:{choch_alcista or choch_bajista} | Quemada:{zona_quemada} | Precio:{precio:.2f}"

        direccion = "Comprar" if condicion_buy else "Vender"
        sl = (ob_bull - 2.5) if direccion == "Comprar" else (ob_bear + 2.5)
        tp1 = precio + 5 if direccion == "Comprar" else precio - 5
        tp2 = precio + 10 if direccion == "Comprar" else precio - 10
        tp3 = precio + 20 if direccion == "Comprar" else precio - 20
        sesion = get_session()
        bos_ok = bos_alcista or bos_bajista; choch_ok = choch_alcista or choch_bajista

    if not es_prueba:
        data["count"] += 1; save_contador(data)

    # Gráfico
    plt.figure(figsize=(11,5.5), dpi=150); plt.style.use('dark_background')
    if len(m1) > 0: plt.plot(m1['Close'].tail(100).values, color='#00ff88', linewidth=1.4, label='Precio 1M')
    plt.axhspan(sl, sl+3 if direccion=="Comprar" else sl-3, color='red', alpha=0.25, label=f'OB {sl:.2f}')
    plt.axhline(precio, color='#00aaff', linestyle='--', linewidth=1.2, label=f'Entrada {precio:.2f}')
    plt.title(f'{sesion} #{data["count"]}/8 | {tendencia_15} | BOS+CHOCH+OB', color='white', fontsize=11)
    plt.legend(loc='upper left', fontsize=7); plt.grid(alpha=0.15); plt.tight_layout()
    plt.savefig('chart.png'); plt.close()

    emoji = "🟢" if direccion == "Comprar" else "🔴"
    mensaje = f"""{emoji} {direccion} XAUUSD 🔥
{sesion} | Tendencia 15M: {tendencia_15}

🛑 SL: {sl:.2f}
🎯 Entrar: {precio:.2f}
✅ TP1: {tp1:.2f}
✅ TP2: {tp2:.2f}
✅ TP3: {tp3:.2f}

BOS:{'✅' if bos_ok else '❌'} | CHOCH 5M:{'✅' if choch_ok else '❌'} | OB 1M:✅ | POI:✅
{'PRUEBA - tu bot si envia a Telegram' if es_prueba else ''}
"""
    enviar_telegram('chart.png', mensaje)
    return f"Señal {direccion} {data['count']}/8 enviada - {precio:.2f} {'(PRUEBA)' if es_prueba else ''}"

@app.route('/')
def home(): return "Bot Sniper Pro BOS CHOCH OB POI Activo"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
