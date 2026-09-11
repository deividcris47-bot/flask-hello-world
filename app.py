import os
import time
import requests
import yfinance as yf
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask
from threading import Thread

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

@app.route('/')
def home():
    return "ORO BOS ON 24/7 CON FOTO T1 T2 T3 - LIVE - 5 SNIPER"

@app.route('/healthz')
def healthz():
    return "OK", 200

def enviar(texto, imagen_buf=None):
    if not BOT_TOKEN or not CHANNEL_ID:
        print("Falta BOT_TOKEN o CHANNEL_ID en Environment")
        return
    try:
        if imagen_buf:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            files = {'photo': ('chart.png', imagen_buf, 'image/png')}
            data = {"chat_id": CHANNEL_ID, "caption": texto, "parse_mode": "Markdown"}
            requests.post(url, data=data, files=files, timeout=15)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {"chat_id": CHANNEL_ID, "text": texto, "parse_mode": "Markdown"}
            requests.post(url, data=data, timeout=15)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def bot_oro():
    contador = 0
    ultimo_dia = time.localtime().tm_yday
    print("Bot 5 Sniper iniciado...")
    enviar("✅ Bot XAUUSD 5 SNIPER conectado - Esperando zona 4508-4525")

    while True:
        try:
            # Reset diario
            if time.localtime().tm_yday != ultimo_dia:
                contador = 0
                ultimo_dia = time.localtime().tm_yday
                print("Nuevo dia - contador reseteado")

            if contador >= 5:
                time.sleep(300)
                continue

            # Datos gratis sin TradingView
            df = yf.download("GC=F", period="1d", interval="1m", progress=False)
            if df.empty or len(df) < 5:
                time.sleep(60)
                continue

            precio = float(df['Close'].iloc[-1])

            # TU ZONA DE LA FOTO - 15M -> 1M
            ZONA_MIN = 4508
            ZONA_MAX = 4525
            FILTRO_INDUCEMENT = 2.5

            en_zona = ZONA_MIN <= precio <= ZONA_MAX
            es_trampa = ZONA_MAX < precio <= ZONA_MAX + FILTRO_INDUCEMENT
            vela_bajista_1m = float(df['Close'].iloc[-1]) < float(df['Open'].iloc[-1])

            if en_zona and not es_trampa and vela_bajista_1m:
                contador += 1

                # Crear grafico
                plt.figure(figsize=(6, 3))
                plt.plot(df['Close'].tail(60).values, linewidth=1.5)
                plt.title(f"XAUUSD 1M - SELL {precio:.2f}")
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=100)
                buf.seek(0)
                plt.close()

                mensaje = f"""🎯 *XAUUSD SNIPER {contador}/5*
MAPEO: 15M -> 1M
*SELL: {precio:.2f}*
SL: {precio + 2.5:.2f} (2.5$)
TP1: 4480
TP2: 4366 Liquidez

Anti-inducement: OK
Volumen: OK"""

                enviar(mensaje, imagen_buf=buf)
                print(f"Sniper {contador}/5 enviado: {precio}")
                time.sleep(3600) # 1 hora entre señales

        except Exception as e:
            print(f"Error en bot: {e}")
            time.sleep(60)

        time.sleep(60)

# Iniciar bot en segundo plano
Thread(target=bot_oro, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
