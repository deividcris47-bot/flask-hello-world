from flask import Flask
import threading, time, os
from datetime import datetime
import pytz
import yfinance as yf
import requests

app = Flask(__name__)

# --- CONFIGURA ESTO ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "PON_AQUI_TU_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID", "PON_AQUI_TU_CHAT_ID")
# ----------------------

LAST_ERROR = "Ninguno"
ULTIMO_PRECIO = 0

def hora_ec():
    return datetime.now(pytz.timezone('America/Guayaquil')).strftime('%Y-%m-%d %H:%M:%S')

def obtener_precio(ticker="GC=F"):
    global LAST_ERROR, ULTIMO_PRECIO
    try:
        df = yf.download(ticker, period="5d", interval="1h", progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 2:
            return None
        try:
            precio = float(df['Close'].iloc[-1])
        except:
            precio = float(df['Close'].iloc[-1].iloc[0])
        ULTIMO_PRECIO = precio
        return precio
    except Exception as e:
        LAST_ERROR = str(e)[:150]
        return None

def enviar_telegram(mensaje):
    try:
        if "PON_AQUI" in TELEGRAM_TOKEN:
            print(f"SIMULACION TELEGRAM (falta token): {mensaje}")
            return True
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        r = requests.post(url, data=data, timeout=10)
        print(f"Telegram enviado: {r.text}")
        return True
    except Exception as e:
        global LAST_ERROR
        LAST_ERROR = f"Telegram: {e}"
        return False

def bot_loop():
    print(">>> BOT DEIVID V8 VIP INICIADO")
    while True:
        try:
            precio = obtener_precio("GC=F")
            print(f"{hora_ec()} - XAU: {precio} - Error: {LAST_ERROR}")

            # Aquí puedes poner tu lógica TP1 TP2 TP3
            # Por ahora solo loguea, para no spamear

            time.sleep(60) # Chequea cada 60 seg
        except Exception as e:
            print(f"Error en bot_loop: {e}")
            time.sleep(60)

# Inicia el bot en segundo plano
threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return f"BOT XAU SENALES DEIVID VIP - ONLINE - {hora_ec()} EC - XAU: {ULTIMO_PRECIO} - Error: {LAST_ERROR}", 200

@app.route('/test')
def test():
    precio = obtener_precio("GC=F")
    if precio is None:
        return f"TEST OK V8 - Bot vivo (Mercado cerrado o sin datos) - {hora_ec()} - Error: {LAST_ERROR}", 200
    return f"TEST OK V8 - Bot vivo - XAU {precio:.2f} - {hora_ec()} EC", 200

@app.route('/enviar_grafico')
def grafico():
    # Señal de prueba para tu canal
    precio = obtener_precio("GC=F")
    if precio is None:
        precio = ULTIMO_PRECIO

    mensaje = f"""
🔥 *XAU/USD SEÑAL VIP DEIVID* 🔥
💰 *Precio:* {precio}
📈 *Dirección:* BUY
🎯 *TP1:* {precio+5 if precio else 0:.2f}
🎯 *TP2:* {precio+10 if precio else 0:.2f}
🎯 *TP3:* {precio+15 if precio else 0:.2f}
🛑 *SL:* {precio-10 if precio else 0:.2f}
⏰ *Hora EC:* {hora_ec()}
"""
    enviar_telegram(mensaje)
    return f"GRAFICO ENVIADO - XAU {precio} - {hora_ec()}", 200

@app.route('/senial_test')
def senial_test():
    enviar_telegram(f"✅ BOT DEIVID VIP CONECTADO - TEST OK - {hora_ec()} EC - XAU: {ULTIMO_PRECIO}")
    return "SEÑAL DE PRUEBA ENVIADA A TELEGRAM", 200

@app.errorhandler(404)
def notfound(e):
    return "BOT DEIVID ONLINE - Usa /test - /enviar_grafico - /senial_test", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
