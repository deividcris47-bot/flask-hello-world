import os, yfinance as yf, pandas as pd, mplfinance as mpf, requests, json, threading, time
from flask import Flask
from datetime import datetime

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
ESTADO_FILE = "/tmp/trade.json"

def enviar(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_data(interval, period):
    df = yf.download("GC=F", period=period, interval=interval, progress=False)
    df.columns = [c.lower() for c in df.columns]
    return df

def bot_loop():
    while True:
        try:
            # 15m BOS+CHOCH+STRONG
            df15 = get_data("15m", "5d")
            precio15 = float(df15['close'].iloc[-1])
            high_20 = df15['high'].iloc[-21:-1].max()
            low_20 = df15['low'].iloc[-21:-1].min()
            if precio15 > high_20: tend, score, strong = "ALCISTA", 6, low_20
            elif precio15 < low_20: tend, score, strong = "BAJISTA", 6, high_20
            else: time.sleep(60); continue

            # 5m OB+FVG
            df5 = get_data("5m", "2d")
            entrada=sl= None
            for i in range(-10,-2):
                v1,v2,v3 = df5.iloc[i-1], df5.iloc[i], df5.iloc[i+1]
                fvg = (v3['low']>v1['high']) if tend=="ALCISTA" else (v3['high']<v1['low'])
                ob = (v2['close']<v2['open'] and v3['close']>v2['high']) if tend=="ALCISTA" else (v2['close']>v2['open'] and v3['close']<v2['low'])
                if fvg and ob:
                    entrada = (v2['low']+v2['high'])/2
                    sl = v2['low']-2 if tend=="ALCISTA" else v2['high']+2
                    break

            if entrada and abs(entrada-precio15) < 10:
                riesgo = abs(entrada-sl)
                tp1, tp2, tp3 = (entrada+riesgo*1, entrada+riesgo*2, entrada+riesgo*3.5) if tend=="ALCISTA" else (entrada-riesgo*1, entrada-riesgo*2, entrada-riesgo*3.5)
                enviar(f"🟢 *Señal {tend} 8/8 - {entrada:.2f}*\n15m: BOS+CHOCH+STRONG | 5m: OB+FVG\n🎯 {entrada:.2f} 🛑 {sl:.2f}\n✅ TP1 {tp1:.2f} | TP2 {tp2:.2f} | TP3 {tp3:.2f}")
                time.sleep(900)
        except: pass
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home(): return "Bot 8/8 activo"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
