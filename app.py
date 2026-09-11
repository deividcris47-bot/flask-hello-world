import os, time, requests, yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "-1004419307514"

@app.route('/')
def home(): 
    return "ORO BOS ON 24/7 CON FOTO T1 T2 T3 - ACTIVO"

@app.route('/healthz')
def healthz(): 
    return "OK", 200

def enviar(msg):
    try:
        if not BOT_TOKEN: return
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHANNEL_ID, "text": msg}, timeout=10)
    except: pass

def enviar_foto(buf, msg):
    try:
        if not BOT_TOKEN: return
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {'photo': ('chart.png', buf, 'image/png')}
        data = {'chat_id': CHANNEL_ID, 'caption': msg, 'parse_mode': 'Markdown'}
        requests.post(url, files=files, data=data, timeout=15)
    except: pass

def get_data():
    try:
        df = yf.download("GC=F", period="5d", interval="15m", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)
        return df
    except: 
        return None

def bot_loop():
    time.sleep(10)
    enviar("🚀 BOT ORO 24/7 INICIADO CON FOTO T1 T2 T3")
    while True:
        try:
            df = get_data()
            if df is None or len(df) < 50: 
                time.sleep(60)
                continue
            high_20 = float(df['High'][-20:-1].max())
            low_20 = float(df['Low'][-20:-1].min())
            price = float(df['Close'].iloc[-1])
            signal = None
            if price > high_20: signal = "BUY"
            elif price < low_20: signal = "SELL"
            if signal:
                plt.figure(figsize=(8,4))
                plt.plot(df['Close'][-50:], color='green' if signal=="BUY" else 'red', linewidth=2)
                plt.title(f"XAUUSD 15m BOS {signal} {price:.2f}")
                plt.grid(True)
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plt.close()
                if signal == "BUY":
                    msg = f"🟢 *COMPRA ORO*\nEntrada: {price:.2f}\nSL: {low_20:.2f}\nTP1: {price+5:.2f}\nTP2: {price+10:.2f}\nTP3: {price+18:.2f}"
                else:
                    msg = f"🔴 *VENTA ORO*\nEntrada: {price:.2f}\nSL: {high_20:.2f}\nTP1: {price-5:.2f}\nTP2: {price-10:.2f}\nTP3: {price-18:.2f}"
                enviar_foto(buf, msg)
                time.sleep(900)
        except Exception as e:
            print(f"Error bot: {e}")
        time.sleep(60)

# ESTO ES LO QUE ARREGLA EL ERROR DE GUNICORN
try:
    Thread(target=bot_loop, daemon=True).start()
except Exception as e:
    print(f"Error iniciando hilo: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
