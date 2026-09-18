import os
import time
import threading
import requests
import yfinance as yf
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask

# ========= CONFIG TENA VIP =========
TOKEN = os.getenv("BOT_TOKEN", "AQUI_TU_TOKEN")
CHAT_ID = os.getenv("CHAT_ID", "AQUI_TU_CHAT_ID")
SYMBOL = "GC=F" # XAU Oro Futuros - más estable que XAUUSD

app = Flask(__name__)
ultima_alerta = {"zona": None, "tiempo": 0}

def enviar_telegram(mensaje, foto_path=None):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
        print(f"Enviado: {mensaje[:50]}")
    except Exception as e:
        print(f"Error telegram: {e}")

def get_data(interval, period="2d"):
    try:
        df = yf.download(SYMBOL, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        return df
    except: return None

def detectar_zona_retesteo(df15):
    if df15 is None or len(df15) < 30: return None, None, False, False
    # LIVE -1 no -2
    high_20 = float(df15['High'].rolling(20).max().iloc[-1])
    low_20 = float(df15['Low'].rolling(20).min().iloc[-1])
    precio_actual = float(df15['Close'].iloc[-1])
    
    # CON 1 TOQUE YA ES ZONA (antes pedía 2)
    toques_high = ((df15['High'].tail(20) >= high_20 - 8) & (df15['High'].tail(20) <= high_20 + 8)).sum()
    toques_low = ((df15['Low'].tail(20) >= low_20 - 8) & (df15['Low'].tail(20) <= low_20 + 8)).sum()
    
    zona_buy = low_20
    zona_sell = high_20
    return zona_buy, zona_sell, toques_low >= 1, toques_high >= 1, precio_actual

def detectar_intencion(df5):
    if df5 is None or len(df5) < 5: return None
    last = df5.iloc[-1] # VELA LIVE - CLAVE PARA QUE NO LLEGUE TARDE
    body = abs(float(last['Open']) - float(last['Close']))
    rango = float(last['High']) - float(last['Low'])
    if rango < 1.2: return None
    cuerpo_grande = body > (rango * 0.45) # más sensible
    if cuerpo_grande and float(last['Close']) < float(last['Open']): return "SELL"
    if cuerpo_grande and float(last['Close']) > float(last['Open']): return "BUY"
    return None

def check_mercado():
    while True:
        try:
            df15 = get_data("15m")
            df5 = get_data("5m", period="1d")
            if df15 is None or df5 is None:
                time.sleep(30); continue

            zona_buy, zona_sell, hay_zona_buy, hay_zona_sell, precio = detectar_zona_retesteo(df15)
            intencion = detectar_intencion(df5)
            
            ahora = time.time()
            # EVITAR SPAM - 15 min entre mismas zonas
            if ahora - ultima_alerta["tiempo"] < 900 and ultima_alerta["zona"] == f"{zona_buy}-{zona_sell}":
                time.sleep(30); continue

            # 1. PRE-AVISO 20 DOLARES ANTES - ESTO ES LO QUE PEDISTE
            if hay_zona_sell and (zona_sell - precio) <= 20 and (zona_sell - precio) > 0:
                enviar_telegram(f"🟡 *PRE-AVISO SELL - SE ACERCA*\n📍 Zona Retesteo 15M: {zona_sell-5:.2f} - {zona_sell+5:.2f}\n💰 Precio actual: {precio:.2f} (a {zona_sell-precio:.2f}$ de la zona)\n👀 Prende gráfica - posible intención en minutos")
                ultima_alerta["zona"] = f"{zona_buy}-{zona_sell}"; ultima_alerta["tiempo"] = ahora

            if hay_zona_buy and (precio - zona_buy) <= 20 and (precio - zona_buy) > 0:
                enviar_telegram(f"🟡 *PRE-AVISO BUY - SE ACERCA*\n📍 Zona Retesteo 15M: {zona_buy-5:.2f} - {zona_buy+5:.2f}\n💰 Precio actual: {precio:.2f} (a {precio-zona_buy:.2f}$ de la zona)\n👀 Prende gráfica - posible intención en minutos")
                ultima_alerta["zona"] = f"{zona_buy}-{zona_sell}"; ultima_alerta["tiempo"] = ahora

            # 2. INTENCION EN ZONA - YA DENTRO
            if hay_zona_sell and abs(precio - zona_sell) <= 8 and intencion == "SELL":
                enviar_telegram(f"⚠️ *INTENCIÓN PARA VENTA DETECTADA*\n📍 Zona Retesteo 15M: {zona_sell-7:.2f} - {zona_sell+3:.2f}\n🎯 Toques en zona + Vela intención 5M bajista LIVE\n💰 Precio: {precio:.2f}\n📉 Esperando CHOCH + BOS + OB + FVG\n⏳ Posible SELL en minutos")

            if hay_zona_buy and abs(precio - zona_buy) <= 8 and intencion == "BUY":
                enviar_telegram(f"⚠️ *INTENCIÓN PARA COMPRA DETECTADA*\n📍 Zona Retesteo 15M: {zona_buy-3:.2f} - {zona_buy+7:.2f}\n🎯 Toques en zona + Vela intención 5M alcista LIVE\n💰 Precio: {precio:.2f}\n📈 Esperando CHOCH + BOS + OB + FVG\n⏳ Posible BUY en minutos")

            time.sleep(30) # CHEQUEA CADA 30 SEGUNDOS - ANTES ERA 60
        except Exception as e:
            print(f"Error loop: {e}"); time.sleep(30)

@app.route('/')
def home(): return "V6.7 OK - Tena Live PRE-ALERTA 30s"

@app.route('/test')
def test():
    enviar_telegram("✅ TEST OK V6.7 - Modo Rapido Activo 30s - Te avisara 20$ antes")
    return "TEST ENVIADO"

# Iniciar hilo
threading.Thread(target=check_mercado, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
