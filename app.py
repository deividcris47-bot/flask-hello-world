import os, time, threading, requests
import yfinance as yf
import pandas as pd
import mplfinance as mpf
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ultima_senal = ""
poi_aviso = {}
bot_iniciado = False

def send_telegram(text, chart_path=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
        print(f"TG SEND: {r.status_code} {r.text[:100]}")
        if chart_path and os.path.exists(chart_path):
            url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(chart_path, 'rb') as f:
                requests.post(url_photo, data={"chat_id": CHAT_ID}, files={"photo": f}, timeout=20)
    except Exception as e:
        print("Error TG:", e)

def get_data():
    try:
        df15 = yf.download("GC=F", period="5d", interval="15m", progress=False)
        df5 = yf.download("GC=F", period="2d", interval="5m", progress=False)
        if df15.empty or df5.empty: return None, None
        if isinstance(df15.columns, pd.MultiIndex): df15.columns = df15.columns.get_level_values(0)
        if isinstance(df5.columns, pd.MultiIndex): df5.columns = df5.columns.get_level_values(0)
        return df15.dropna(), df5.dropna()
    except: return None, None

def analizar():
    global ultima_senal, poi_aviso
    df15, df5 = get_data()
    if df15 is None or len(df15) < 60: return
    precio = float(df5['Close'].iloc[-1])
    high_15 = float(df15['High'].rolling(20).max().iloc[-2])
    low_15 = float(df15['Low'].rolling(20).min().iloc[-2])
    dist_high = abs(precio - high_15)
    dist_low = abs(precio - low_15)
    zona_cercana = None
    tipo_esperado = None
    if dist_high < 5:
        zona_cercana = high_15
        tipo_esperado = "SELL"
    elif dist_low < 5:
        zona_cercana = low_15
        tipo_esperado = "BUY"
    if zona_cercana:
        zona_round = round(zona_cercana, 1)
        if poi_aviso.get("zona") != zona_round:
            poi_aviso = {"zona": zona_round}
            msg = f"⚠️ *RADAR V5 - POI FORMÁNDOSE* ⏳\n\n📍 Zona POI: {zona_cercana:.2f}\n💰 Precio actual: {precio:.2f}\n👀 Tipo esperado: {tipo_esperado}\n\n⛔ *NO ENTRAR AÚN*\n✅ Solo alístate"
            send_telegram(msg)
    bos_buy = precio > high_15 + 1.0
    bos_sell = precio < low_15 - 1.0
    if bos_buy or bos_sell:
        direccion = "BUY" if bos_buy else "SELL"
        entrada = precio
        if direccion == "BUY":
            sl = entrada - 8
            t1, t2, t3 = entrada + 6, entrada + 12, entrada + 20
        else:
            sl = entrada + 8
            t1, t2, t3 = entrada - 6, entrada - 12, entrada - 20
        senal_id = f"{direccion}_{round(entrada/2)*2}"
        if senal_id != ultima_senal:
            ultima_senal = senal_id
            chart_path = "/tmp/chart.png"
            try:
                mpf.plot(df5.tail(60), type='candle', style='yahoo', savefig=chart_path)
            except: chart_path = None
            msg = f"🚨 *SEÑAL {direccion} CONFIRMADA V5.1* 🚨\n\n🎯 Entrada: {entrada:.2f}\n🛑 SL: {sl:.2f}\n✅ TP1: {t1:.2f}\n✅ TP2: {t2:.2f}\n✅ TP3: {t3:.2f}\n\n🔥 ¡ENTRA AHORA!"
            send_telegram(msg, chart_path)

def loop():
    while True:
        try: analizar()
        except Exception as e: print("Error loop", e)
        time.sleep(300)

threading.Thread(target=loop, daemon=True).start()

@app.route('/')
def home():
    global bot_iniciado
    if not bot_iniciado:
        bot_iniciado = True
        send_telegram("✅ *V5.1 PRO + RADAR ACTIVADO* ✅\n\n15M Análisis / 5M Gatillo\nPOI + BOS + OB + FVG\n\nEl bot se activó al abrir la web. Ya estoy cazando ORO 24/7 🔥")
    return "V5 PRO + RADAR ACTIVO - Tena - OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
