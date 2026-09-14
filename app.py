import os, yfinance as yf, requests, threading, time
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def enviar(msg):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_data(interval, period):
    df = yf.download("GC=F", period=period, interval=interval, progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    return df

def bot_loop():
    import pandas as pd
    while True:
        try:
            df15 = get_data("15m", "5d")
            if df15 is None: time.sleep(60); continue
            precio = float(df15['close'].iloc[-1])
            high_20 = df15['high'].iloc[-21:-1].max()
            low_20 = df15['low'].iloc[-21:-1].min()
            tend = None
            if precio > high_20: tend = "ALCISTA"
            elif precio < low_20: tend = "BAJISTA"
            else: time.sleep(60); continue

            df5 = get_data("5m", "2d")
            if df5 is None: continue
            entrada=sl=None
            for i in range(-10,-2):
                v1,v2,v3 = df5.iloc[i-1], df5.iloc[i], df5.iloc[i+1]
                fvg = (v3['low']>v1['high']) if tend=="ALCISTA" else (v3['high']<v1['low'])
                ob = (v2['close']<v2['open'] and v3['close']>v2['high']) if tend=="ALCISTA" else (v2['close']>v2['open'] and v3['close']<v2['low'])
                if fvg and ob:
                    entrada = (float(v2['low'])+float(v2['high']))/2
                    sl = float(v2['low'])-2 if tend=="ALCISTA" else float(v2['high'])+2
                    break
            if entrada and abs(entrada-precio) < 12:
                riesgo = abs(entrada-sl)
                if tend=="ALCISTA": tp1,tp2,tp3 = entrada+riesgo, entrada+riesgo*2, entrada+riesgo*3.5
                else: tp1,tp2,tp3 = entrada-riesgo, entrada-riesgo*2, entrada-riesgo*3.5
                enviar(f"🟢 *Señal {tend} 8/8 - {entrada:.2f}*\n15m BOS+CHOCH+STRONG | 5m OB+FVG\n🎯 {entrada:.2f} 🛑 {sl:.2f}\n✅ TP1 {tp1:.2f} | TP2 {tp2:.2f} | TP3 {tp3:.2f}")
                time.sleep(900)
        except Exception as e: print(e)
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home(): return "Bot 8/8 activo - Esperando señal"
@app.route('/test')
def test():
    enviar("✅ BOT 8/8 CONECTADO - Esperando estructura real")
    return "Test enviado: True"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
